import { NestFactory } from '@nestjs/core';

import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix('api'); // 统一添加 /api 前缀，匹配前端代理
  app.enableCors({
    credentials: true,
    origin: true,
  });
  await app.listen(3000);
}
bootstrap();
