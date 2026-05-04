import { eventHandler } from 'h3';
import { useResponseSuccess } from '~/utils/response';

export default eventHandler(() => {
  const tags = [
    {
      id: 1,
      source_type: 'system',
      tag_code: 'JD_SELF_OPERATED',
      tag_name: '京东自营',
      tag_type: 'platform',
    },
    {
      id: 2,
      source_type: 'system',
      tag_code: 'TMALL_FLAGSHIP',
      tag_name: '天猫旗舰店',
      tag_type: 'platform',
    },
    {
      id: 3,
      source_type: 'user',
      tag_code: 'HIGH_PROFIT',
      tag_name: '高利润',
      tag_type: 'business',
    },
    {
      id: 4,
      source_type: 'system',
      tag_code: 'HOT_SALE',
      tag_name: '热销',
      tag_type: 'marketing',
    },
    {
      id: 5,
      source_type: 'system',
      tag_code: 'NEW_ARRIVAL',
      tag_name: '新品',
      tag_type: 'marketing',
    },
  ];

  return useResponseSuccess(tags);
});
