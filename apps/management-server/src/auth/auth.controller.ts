import { Controller, Post, Get, Body } from '@nestjs/common';
import { AuthService } from './auth.service';

@Controller()
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  // 对应 /api/auth/login
  @Post('auth/login')
  async login(@Body() body: any) {
    const data = await this.authService.login(body.username);
    return {
      code: 0,
      data,
      message: 'ok',
    };
  }

  // 对应 /api/user/info
  @Get('user/info')
  async getUserInfo() {
    const data = await this.authService.getUserInfo();
    return {
      code: 0,
      data,
      message: 'ok',
    };
  }

  // 对应 /api/auth/codes
  @Get('auth/codes')
  async getAccessCodes() {
    const data = await this.authService.getAccessCodes();
    return {
      code: 0,
      data,
      message: 'ok',
    };
  }
}
