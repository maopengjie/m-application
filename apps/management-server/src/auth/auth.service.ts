import {
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';

type AuthUser = {
  avatar: string;
  desc: string;
  homePath: string;
  id: string;
  password: string;
  realName: string;
  username: string;
};

const defaultAccessCodes = ['super'];

const defaultMenus = [
  {
    component: 'BasicLayout',
    meta: {
      icon: 'lucide:layout-dashboard',
      order: -1,
      title: '仪表盘',
    },
    name: 'Dashboard',
    path: '/dashboard',
    children: [
      {
        component: '/dashboard/analytics/index',
        meta: {
          affixTab: true,
          icon: 'lucide:area-chart',
          title: '分析页',
        },
        name: 'Analytics',
        path: '/analytics',
      },
      {
        component: '/dashboard/workspace/index',
        meta: {
          icon: 'carbon:workspace',
          title: '工作台',
        },
        name: 'Workspace',
        path: '/workspace',
      },
    ],
  },
  {
    component: 'BasicLayout',
    meta: {
      icon: 'ic:baseline-view-in-ar',
      keepAlive: true,
      order: 1000,
      title: '演示',
    },
    name: 'Demos',
    path: '/demos',
    children: [
      {
        component: '/demos/element/index',
        meta: {
          title: 'Element Plus',
        },
        name: 'ElementDemos',
        path: '/demos/element',
      },
      {
        component: '/demos/form/basic',
        meta: {
          title: '表单演示',
        },
        name: 'BasicForm',
        path: '/demos/form',
      },
    ],
  },
];

@Injectable()
export class AuthService {
  private readonly sampleRefreshToken = 'sample-refresh-token-vben-nest';
  private readonly user: AuthUser = {
    avatar: 'https://unpkg.com/@vben/static-source@0.1.7/avatar/vben-logo.png',
    desc: 'Initialize repository scaffold',
    homePath: '/analytics',
    id: '1',
    password: '123456',
    realName: 'Vben Admin',
    username: 'vben',
  };

  async login(username?: string, password?: string) {
    const normalizedUsername = username?.trim() || this.user.username;

    if (
      normalizedUsername !== this.user.username ||
      (password && password !== this.user.password)
    ) {
      throw new UnauthorizedException('Username or password is invalid');
    }

    return {
      accessToken: this.createAccessToken(this.user.username),
      refreshToken: this.sampleRefreshToken,
      username: this.user.username,
      realName: this.user.realName,
      roles: defaultAccessCodes,
      desc: this.user.desc,
    };
  }

  async refreshToken(cookieHeader: string) {
    const refreshToken = this.extractRefreshToken(cookieHeader);

    if (refreshToken !== this.sampleRefreshToken) {
      throw new UnauthorizedException('Refresh token is invalid');
    }

    return {
      accessToken: this.createAccessToken('vben'),
      refreshToken: this.sampleRefreshToken,
    };
  }

  async logout() {
    return true;
  }

  async getUserInfo() {
    return {
      avatar: this.user.avatar,
      desc: this.user.desc,
      homePath: this.user.homePath,
      id: this.user.id,
      roles: defaultAccessCodes,
      username: this.user.username,
      realName: this.user.realName,
    };
  }

  async updateUserInfo(data: any) {
    if (typeof data?.realName === 'string' && data.realName.trim()) {
      this.user.realName = data.realName.trim();
    }
    if (typeof data?.avatar === 'string' && data.avatar.trim()) {
      this.user.avatar = data.avatar.trim();
    }
    if (typeof data?.desc === 'string') {
      this.user.desc = data.desc;
    } else if (typeof data?.introduction === 'string') {
      this.user.desc = data.introduction;
    }

    return this.getUserInfo();
  }

  async getAccessCodes() {
    return defaultAccessCodes;
  }

  async getAllMenus() {
    return defaultMenus;
  }

  private createAccessToken(username: string) {
    return `sample-access-token-vben-nest-${username || 'vben'}`;
  }

  private extractRefreshToken(cookieHeader: string) {
    const cookies = cookieHeader
      .split(';')
      .map((item) => item.trim())
      .filter(Boolean);

    const refreshTokenCookie = cookies.find((item) =>
      item.startsWith('refresh_token='),
    );

    return refreshTokenCookie?.split('=')[1] ?? '';
  }
}
