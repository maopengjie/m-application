from __future__ import annotations

import re

from sqlalchemy.orm import Session

from models import CategoryNode, MappingRule, SkuComparison, SkuProduct, SkuProductAttr


def _matches_rule_category(db: Session, product: SkuProduct, category_id: int | None) -> bool:
    if not category_id:
        return True

    category = db.query(CategoryNode).filter(CategoryNode.id == category_id).first()
    if category is None:
        return False

    if category.level == 1:
        return product.category_level_1 == category.name
    if category.level == 2:
        return product.category_level_2 == category.name
    if category.level == 3:
        if category.external_id and category.external_id.isdigit() and product.category_id_3 is not None:
            return product.category_id_3 == int(category.external_id)
        return product.category_level_3 == category.name
    return False

def apply_mapping_rules_to_product(db: Session, product: SkuProduct):
    """
    Applies active mapping rules to a product's name to determine its normalized_name.
    """
    rules = (
        db.query(MappingRule)
        .filter(MappingRule.is_active == 1)
        .order_by(MappingRule.priority.desc(), MappingRule.id.desc())
        .all()
    )
    
    current_name = product.product_name
    for rule in rules:
        # Check if platform matches (if specified)
        if rule.platform and rule.platform != product.platform:
            continue
            
        if not _matches_rule_category(db, product, rule.category_id):
            continue
        
        if rule.rule_type == "KEYWORD":
            if rule.pattern.lower() in current_name.lower():
                product.normalized_name = rule.unified_label
                return True
        elif rule.rule_type == "REGEX":
            try:
                if re.search(rule.pattern, current_name, re.IGNORECASE):
                    product.normalized_name = rule.unified_label
                    return True
            except re.error:
                continue
                
    # If no rules match, we keep the original name or set to product_name
    product.normalized_name = product.product_name
    return False


def _clean_match_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", " ", value)).strip().lower()


def _extract_name_tokens(product: SkuProduct) -> set[str]:
    source = " ".join(
        part
        for part in [product.normalized_name, product.product_name]
        if part
    )
    cleaned = _clean_match_text(source)
    if not cleaned:
        return set()
    return {token for token in cleaned.split(" ") if len(token) >= 2}


def _extract_spec_tokens(product: SkuProduct, attrs: list[SkuProductAttr]) -> set[str]:
    parts = [product.normalized_name or "", product.product_name or ""]
    parts.extend(
        f"{attr.attr_name} {attr.attr_value or ''} {attr.attr_unit or ''}"
        for attr in attrs
    )
    source = " ".join(parts)
    specs = set(
        re.findall(
            r"(?:\d+(?:\.\d+)?(?:gb|g|kg|ml|l|寸|英寸|hz|w|tb)|rtx\s?\d{3,4}|i[3579]|gen\s?\d+|a\d{2}|骁龙\d+\s?gen\d+|pro|max|plus|ultra)",
            source,
            flags=re.IGNORECASE,
        )
    )
    normalized_specs = {_clean_match_text(item) for item in specs}
    return {item for item in normalized_specs if item}


def _score_brand_match(left: SkuProduct, right: SkuProduct) -> int:
    left_brand = _clean_match_text(left.brand_name)
    right_brand = _clean_match_text(right.brand_name)
    if not left_brand or not right_brand:
        return 0
    if left_brand == right_brand:
        return 35
    if left_brand in right_brand or right_brand in left_brand:
        return 25
    return 0


def _score_name_match(left: SkuProduct, right: SkuProduct) -> int:
    left_name = _clean_match_text(left.normalized_name or left.product_name)
    right_name = _clean_match_text(right.normalized_name or right.product_name)
    if not left_name or not right_name:
        return 0
    if left_name == right_name:
        return 35

    left_tokens = _extract_name_tokens(left)
    right_tokens = _extract_name_tokens(right)
    if not left_tokens or not right_tokens:
        return 0

    overlap = len(left_tokens & right_tokens)
    base = max(len(left_tokens), len(right_tokens))
    return min(35, round(overlap * 35 / base))


def _score_spec_match(left_specs: set[str], right_specs: set[str]) -> int:
    if not left_specs or not right_specs:
        return 0
    overlap = len(left_specs & right_specs)
    if overlap <= 0:
        return 0
    base = max(len(left_specs), len(right_specs))
    return min(30, round(overlap * 30 / base))


def _score_product_match(
    left: SkuProduct,
    right: SkuProduct,
    left_attrs: list[SkuProductAttr],
    right_attrs: list[SkuProductAttr],
) -> int:
    if left.platform == right.platform and left.sku_id == right.sku_id:
        return 0
    if left.category_level_1 and right.category_level_1 and left.category_level_1 != right.category_level_1:
        return 0

    brand_score = _score_brand_match(left, right)
    name_score = _score_name_match(left, right)
    spec_score = _score_spec_match(
        _extract_spec_tokens(left, left_attrs),
        _extract_spec_tokens(right, right_attrs),
    )
    category_bonus = 0
    if left.category_level_3 and right.category_level_3 and left.category_level_3 == right.category_level_3:
        category_bonus = 10

    total_score = min(100, brand_score + name_score + spec_score + category_bonus)
    return total_score


def explain_product_match(
    left: SkuProduct,
    right: SkuProduct,
    left_attrs: list[SkuProductAttr],
    right_attrs: list[SkuProductAttr],
) -> tuple[int, list[str]]:
    if left.platform == right.platform and left.sku_id == right.sku_id:
        return 0, ["同平台同 SKU，不参与竞品匹配"]
    if left.category_level_1 and right.category_level_1 and left.category_level_1 != right.category_level_1:
        return 0, [f"一级类目不一致：{left.category_level_1} / {right.category_level_1}"]

    reasons: list[str] = []
    brand_score = _score_brand_match(left, right)
    name_score = _score_name_match(left, right)
    left_specs = _extract_spec_tokens(left, left_attrs)
    right_specs = _extract_spec_tokens(right, right_attrs)
    spec_overlap = sorted(left_specs & right_specs)
    spec_score = _score_spec_match(left_specs, right_specs)
    category_bonus = 0

    if brand_score > 0:
        reasons.append(f"品牌匹配 +{brand_score}")
    if name_score > 0:
        reasons.append(f"归一名/标题相似 +{name_score}")
    if spec_score > 0:
        detail = f"规格词重合 +{spec_score}"
        if spec_overlap:
            detail = f"{detail}（{', '.join(spec_overlap[:4])}）"
        reasons.append(detail)
    if left.category_level_3 and right.category_level_3 and left.category_level_3 == right.category_level_3:
        category_bonus = 10
        reasons.append("三级类目一致 +10")
    if not reasons:
        reasons.append("缺少足够的品牌、归一名或规格重合信号")

    total_score = min(100, brand_score + name_score + spec_score + category_bonus)
    return total_score, reasons


def auto_match_comparisons(db: Session) -> int:
    """
    Finds cross-platform matching products via brand, normalized name,
    and spec-keyword scoring, then creates or updates AUTO comparisons.
    """
    products = db.query(SkuProduct).filter(SkuProduct.status == 1).all()
    attrs = db.query(SkuProductAttr).all()
    attr_map: dict[int, list[SkuProductAttr]] = {}
    for attr in attrs:
        attr_map.setdefault(attr.sku_product_id, []).append(attr)

    match_count = 0
    review_threshold = 60
    high_confidence_threshold = 85
    for index, left in enumerate(products):
        for right in products[index + 1 :]:
            if left.platform == right.platform:
                continue

            score, _ = explain_product_match(
                left,
                right,
                attr_map.get(left.id, []),
                attr_map.get(right.id, []),
            )
            existing = db.query(SkuComparison).filter(
                ((SkuComparison.master_sku_id == left.id) & (SkuComparison.linked_sku_id == right.id))
                | ((SkuComparison.master_sku_id == right.id) & (SkuComparison.linked_sku_id == left.id))
            ).first()

            master = left if left.platform == "jd" else right
            linked = right if left.platform == "jd" else left
            next_status = 1 if score >= high_confidence_threshold else 0 if score >= review_threshold else -1

            if score < review_threshold:
                if existing and existing.match_type != "MANUAL":
                    existing.master_sku_id = master.id
                    existing.linked_sku_id = linked.id
                    existing.match_score = score
                    existing.match_type = "AUTO"
                    existing.status = -1
                continue

            if existing:
                if existing.match_type == "MANUAL":
                    continue
                existing.master_sku_id = master.id
                existing.linked_sku_id = linked.id
                existing.match_score = score
                existing.match_type = "AUTO"
                existing.status = next_status
                match_count += 1
                continue

            db.add(
                SkuComparison(
                    master_sku_id=master.id,
                    linked_sku_id=linked.id,
                    match_score=score,
                    match_type="AUTO",
                    status=next_status,
                )
            )
            match_count += 1

    db.commit()
    return match_count

def apply_rules_to_all_products(db: Session) -> int:
    """
    Batch applies mapping rules to all products.
    Returns the number of products updated.
    """
    products = db.query(SkuProduct).all()
    count = 0
    for product in products:
        if apply_mapping_rules_to_product(db, product):
            count += 1
    db.commit()
    return count
