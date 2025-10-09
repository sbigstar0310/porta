import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../bloc/auth/auth_bloc.dart';
import '../bloc/auth/auth_event.dart';
import '../bloc/auth/auth_state.dart';
import '../constants/colors.dart';
import '../widgets/email_verification_banner.dart';

class HomeScreen extends StatefulWidget {
  final Widget child;

  const HomeScreen({super.key, required this.child});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String get _currentRoute {
    final location = GoRouterState.of(context).uri.path;
    if (location.startsWith('/agent')) return '/agent';
    if (location.startsWith('/position')) return '/position';
    if (location.startsWith('/health')) return '/health';
    return '/portfolio';
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeApp();
    });
  }

  void _initializeApp() {
    // AuthBloc은 앱 시작 시 자동으로 초기화됨
    // 필요시 추가적인 초기화 로직을 여기에 추가
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is AuthEmailVerificationSuccessState) {
          // 이메일 인증 성공 알림 표시
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(state.message),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 3),
            ),
          );
        }
      },
      child: Scaffold(
        backgroundColor: isDark
            ? AppColors.darkBackground
            : AppColors.neutralGray50,
        body: Column(
          children: [
            // Modern AppBar with glassmorphism effect
            Container(
              decoration: BoxDecoration(
                gradient: isDark
                    ? LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          AppColors.darkSurface,
                          AppColors.darkSurface.withOpacity(0.95),
                        ],
                      )
                    : LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [Colors.white, Colors.white.withOpacity(0.95)],
                      ),
                boxShadow: [
                  BoxShadow(
                    color: isDark
                        ? Colors.black.withOpacity(0.3)
                        : AppColors.shadowLight,
                    blurRadius: 20,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: SafeArea(
                child: Column(
                  children: [
                    // Top header with logo and profile
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 20,
                      ),
                      child: Row(
                        children: [
                          // Logo and brand
                          Row(
                            children: [
                              Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                  gradient: AppColors.primaryGradient,
                                  borderRadius: BorderRadius.circular(12),
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppColors.primaryBlue.withOpacity(
                                        0.3,
                                      ),
                                      blurRadius: 8,
                                      offset: const Offset(0, 2),
                                    ),
                                  ],
                                ),
                                child: const Icon(
                                  Icons.analytics_outlined,
                                  size: 20,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Porta',
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleLarge
                                        ?.copyWith(
                                          fontWeight: FontWeight.bold,
                                          color: isDark
                                              ? Colors.white
                                              : AppColors.neutralGray900,
                                          letterSpacing: -0.5,
                                        ),
                                  ),
                                  Text(
                                    'AI 투자 플랫폼',
                                    style: Theme.of(context).textTheme.bodySmall
                                        ?.copyWith(
                                          color: isDark
                                              ? AppColors.neutralGray400
                                              : AppColors.neutralGray600,
                                          fontSize: 11,
                                        ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          const Spacer(),

                          // Profile section
                          BlocConsumer<AuthBloc, AuthState>(
                            listener: (context, state) {
                              if (state is AuthUnauthenticated) {
                                context.go('/login');
                              }
                            },
                            builder: (context, state) {
                              if (state is AuthAuthenticated ||
                                  state is AuthEmailNotVerified) {
                                final user = state is AuthAuthenticated
                                    ? state.user
                                    : (state as AuthEmailNotVerified).user;
                                return _buildProfileMenu(context, user, isDark);
                              }
                              return Container();
                            },
                          ),
                        ],
                      ),
                    ),

                    // Modern navigation tabs
                    Container(
                      margin: const EdgeInsets.symmetric(horizontal: 24),
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: isDark
                            ? AppColors.darkSurfaceVariant.withOpacity(0.5)
                            : AppColors.neutralGray100,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            _buildModernNavTab(
                              context,
                              '포트폴리오',
                              Icons.account_balance_wallet_outlined,
                              '/portfolio',
                              isDark,
                            ),
                            _buildModernNavTab(
                              context,
                              'AI 에이전트',
                              Icons.psychology_outlined,
                              '/agent',
                              isDark,
                            ),
                            _buildModernNavTab(
                              context,
                              '포지션',
                              Icons.trending_up_outlined,
                              '/position',
                              isDark,
                            ),
                            _buildModernNavTab(
                              context,
                              '시스템',
                              Icons.monitor_heart_outlined,
                              '/health',
                              isDark,
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
            // Email verification banner (AuthEmailNotVerified 상태일 때만 표시)
            BlocBuilder<AuthBloc, AuthState>(
              builder: (context, state) {
                if (state is AuthEmailNotVerified) {
                  return EmailVerificationBanner(user: state.user);
                }
                return const SizedBox.shrink();
              },
            ),
            // Main content
            Expanded(
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1200),
                  child: BlocBuilder<AuthBloc, AuthState>(
                    builder: (context, state) {
                      if (state is AuthLoading) {
                        return const Center(child: CircularProgressIndicator());
                      }

                      if (state is AuthError) {
                        return Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                state.message,
                                style: TextStyle(
                                  color: Theme.of(context).colorScheme.error,
                                ),
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: () => context.read<AuthBloc>().add(
                                  AuthInitialized(),
                                ),
                                child: const Text('다시 시도'),
                              ),
                            ],
                          ),
                        );
                      }

                      return widget.child;
                    },
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileMenu(BuildContext context, dynamic user, bool isDark) {
    return PopupMenuButton<String>(
      offset: const Offset(0, 50),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isDark
              ? AppColors.darkSurfaceVariant.withOpacity(0.5)
              : AppColors.neutralGray100,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isDark ? AppColors.neutralGray600 : AppColors.neutralGray200,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                gradient: AppColors.primaryGradient,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(Icons.person_outline, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 8),
            Icon(
              Icons.keyboard_arrow_down_outlined,
              color: isDark
                  ? AppColors.neutralGray400
                  : AppColors.neutralGray600,
              size: 16,
            ),
          ],
        ),
      ),
      onSelected: (value) {
        if (value == 'logout') {
          context.read<AuthBloc>().add(AuthLogoutRequested());
        } else if (value == 'settings') {
          context.go('/settings');
        }
      },
      itemBuilder: (BuildContext context) {
        return [
          PopupMenuItem<String>(
            value: 'profile',
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  Icon(
                    Icons.person_outline,
                    color: isDark
                        ? AppColors.neutralGray300
                        : AppColors.neutralGray600,
                    size: 20,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '계정',
                          style: TextStyle(
                            fontWeight: FontWeight.w500,
                            color: isDark
                                ? Colors.white
                                : AppColors.neutralGray900,
                          ),
                        ),
                        Text(
                          user.email ?? 'unknown@email.com',
                          style: TextStyle(
                            fontSize: 12,
                            color: isDark
                                ? AppColors.neutralGray400
                                : AppColors.neutralGray600,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const PopupMenuDivider(),
          PopupMenuItem<String>(
            value: 'settings',
            child: Row(
              children: [
                Icon(
                  Icons.settings_outlined,
                  color: isDark
                      ? AppColors.neutralGray300
                      : AppColors.neutralGray600,
                  size: 20,
                ),
                const SizedBox(width: 12),
                Text(
                  '설정',
                  style: TextStyle(
                    color: isDark ? Colors.white : AppColors.neutralGray900,
                  ),
                ),
              ],
            ),
          ),
          PopupMenuItem<String>(
            value: 'logout',
            child: Row(
              children: [
                Icon(Icons.logout_outlined, color: AppColors.error, size: 20),
                const SizedBox(width: 12),
                Text('로그아웃', style: TextStyle(color: AppColors.error)),
              ],
            ),
          ),
        ];
      },
    );
  }

  Widget _buildModernNavTab(
    BuildContext context,
    String title,
    IconData icon,
    String route,
    bool isDark,
  ) {
    final isSelected = _currentRoute == route;

    return GestureDetector(
      onTap: () => context.go(route),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(right: 4),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected
              ? (isDark ? AppColors.primaryBlueAccent : AppColors.primaryBlue)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color:
                        (isDark
                                ? AppColors.primaryBlueAccent
                                : AppColors.primaryBlue)
                            .withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected
                  ? Colors.white
                  : (isDark
                        ? AppColors.neutralGray400
                        : AppColors.neutralGray600),
              size: 18,
            ),
            const SizedBox(width: 8),
            Text(
              title,
              style: TextStyle(
                color: isSelected
                    ? Colors.white
                    : (isDark
                          ? AppColors.neutralGray300
                          : AppColors.neutralGray700),
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
