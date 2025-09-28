import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../bloc/auth/auth_bloc.dart';
import '../bloc/auth/auth_event.dart';
import '../bloc/auth/auth_state.dart';
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
    return Scaffold(
      body: Column(
        children: [
          // Custom AppBar with navigation tabs
          Container(
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              children: [
                // Top bar with title and profile
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 16,
                  ),
                  child: Row(
                    children: [
                      Text(
                        'Porta',
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                      ),
                      const Spacer(),
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
                            return PopupMenuButton<String>(
                              offset: const Offset(0, 40),
                              icon: CircleAvatar(
                                backgroundColor: Theme.of(
                                  context,
                                ).colorScheme.primary,
                                child: Icon(
                                  Icons.person,
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onPrimary,
                                ),
                              ),
                              onSelected: (value) {
                                if (value == 'logout') {
                                  context.read<AuthBloc>().add(
                                    AuthLogoutRequested(),
                                  );
                                } else if (value == 'settings') {
                                  context.go('/settings');
                                }
                              },
                              itemBuilder: (BuildContext context) {
                                return [
                                  PopupMenuItem<String>(
                                    value: 'profile',
                                    child: Row(
                                      children: [
                                        const Icon(Icons.person_outline),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Text(
                                            user.email ?? 'unknown@email.com',
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  const PopupMenuItem<String>(
                                    value: 'settings',
                                    child: Row(
                                      children: [
                                        Icon(Icons.settings_outlined),
                                        SizedBox(width: 12),
                                        Text('설정'),
                                      ],
                                    ),
                                  ),
                                  const PopupMenuDivider(),
                                  const PopupMenuItem<String>(
                                    value: 'logout',
                                    child: Row(
                                      children: [
                                        Icon(Icons.logout_outlined),
                                        SizedBox(width: 12),
                                        Text('로그아웃'),
                                      ],
                                    ),
                                  ),
                                ];
                              },
                            );
                          }
                          return Container();
                        },
                      ),
                    ],
                  ),
                ),
                // Navigation tabs
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _buildNavTab(
                          context,
                          '포트폴리오',
                          Icons.account_balance_wallet_outlined,
                          '/portfolio',
                        ),
                        const SizedBox(width: 24),
                        _buildNavTab(
                          context,
                          '에이전트',
                          Icons.smart_toy_outlined,
                          '/agent',
                        ),
                        const SizedBox(width: 24),
                        _buildNavTab(
                          context,
                          '포지션 관리',
                          Icons.business_outlined,
                          '/position',
                        ),
                        const SizedBox(width: 24),
                        _buildNavTab(
                          context,
                          '시스템 상태',
                          Icons.health_and_safety_outlined,
                          '/health',
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
              ],
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
    );
  }

  Widget _buildNavTab(
    BuildContext context,
    String title,
    IconData icon,
    String route,
  ) {
    final isSelected = _currentRoute == route;

    return InkWell(
      onTap: () => context.go(route),
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          color: isSelected
              ? Theme.of(context).colorScheme.primary.withOpacity(0.1)
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected
                  ? Theme.of(context).colorScheme.primary
                  : Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              title,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                color: isSelected
                    ? Theme.of(context).colorScheme.primary
                    : Theme.of(context).colorScheme.onSurface.withOpacity(0.8),
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
