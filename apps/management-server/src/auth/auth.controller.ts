import type { Request, Response } from 'express';

import { Body, Controller, Get, Post, Req, Res } from '@nestjs/common';
import { AuthService } from './auth.service';

@Controller()
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  // 对应 /api/auth/login
  @Post('auth/login')
  async login(
    @Body() body: any,
    @Res({ passthrough: true }) response: Response,
  ) {
    const data = await this.authService.login(body.username, body.password);
    response.cookie('refresh_token', data.refreshToken, {
      httpOnly: true,
      maxAge: 7 * 24 * 60 * 60 * 1000,
      path: '/',
      sameSite: 'lax',
    });
    return {
      code: 0,
      data: {
        accessToken: data.accessToken,
      },
      message: 'ok',
    };
  }

  // 对应 /api/auth/refresh
  @Post('auth/refresh')
  async refresh(
    @Req() request: Request,
    @Res({ passthrough: true }) response: Response,
  ) {
    const data = await this.authService.refreshToken(
      request.headers.cookie ?? '',
    );
    response.cookie('refresh_token', data.refreshToken, {
      httpOnly: true,
      maxAge: 7 * 24 * 60 * 60 * 1000,
      path: '/',
      sameSite: 'lax',
    });
    return {
      code: 0,
      data: data.accessToken,
      message: 'ok',
    };
  }

  // 对应 /api/auth/logout
  @Post('auth/logout')
  async logout(@Res({ passthrough: true }) response: Response) {
    response.clearCookie('refresh_token', {
      httpOnly: true,
      path: '/',
      sameSite: 'lax',
    });
    await this.authService.logout();
    return {
      code: 0,
      data: true,
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

  @Post('user/update')
  async updateUserInfo(@Body() body: any) {
    const data = await this.authService.updateUserInfo(body);
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

  // 对应 /api/menu/all
  @Get('menu/all')
  async getAllMenus() {
    const data = await this.authService.getAllMenus();
    return {
      code: 0,
      data,
      message: 'ok',
    };
  }
}
