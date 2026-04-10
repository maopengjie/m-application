import { Injectable } from '@nestjs/common';

@Injectable()
export class AuthService {
  async login(username: string) {
    // 模拟成功返回，实际开发时需在此验证密码并生成 JWT
    return {
      accessToken: 'sample-access-token-vben-nest',
      refreshToken: 'sample-refresh-token-vben-nest',
      username,
      realName: 'Vben Admin',
      roles: ['super'],
      desc: 'manager',
    };
  }

  async getUserInfo() {
    return {
      id: '1',
      username: 'vben',
      realName: 'Vben Admin',
      avatar: 'https://unpkg.com/@vben/static-source@0.1.7/avatar/vben-logo.png',
      desc: 'manager',
      roles: ['super'],
    };
  }

  async getAccessCodes() {
     // 返回权限码数组
    return ['AC_1001', 'AC_1002', 'super'];
  }
}
