import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'bloc/auth/auth_bloc.dart';
import 'bloc/auth/auth_event.dart';
import 'bloc/auth/auth_state.dart';
import 'bloc/portfolio/portfolio_bloc.dart';
import 'bloc/agent/agent_bloc.dart';
import 'bloc/position/position_bloc.dart';
import 'bloc/health/health_bloc.dart';
import 'bloc/settings/settings_bloc.dart';
import 'bloc/settings/settings_event.dart';
import 'bloc/settings/settings_state.dart';
import 'services/storage_service.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/register_screen.dart';
import 'screens/home_screen.dart';
import 'screens/portfolio/portfolio_screen.dart';
import 'screens/portfolio/portfolio_edit_screen.dart';
import 'screens/position/position_list_screen.dart';
import 'screens/position/position_manage_screen.dart';
import 'screens/health/health_screen.dart';
import 'screens/agent/agent_screen.dart';
import 'screens/settings/settings_screen.dart';

class PortaApp extends StatefulWidget {
  const PortaApp({super.key});

  @override
  State<PortaApp> createState() => _PortaAppState();
}

class _PortaAppState extends State<PortaApp> {
  @override
  void initState() {
    super.initState();
    _initializeServices();
  }

  Future<void> _initializeServices() async {
    await StorageService.init();
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (context) => AuthBloc()..add(AuthInitialized())),
        BlocProvider(create: (context) => PortfolioBloc()),
        BlocProvider(create: (context) => AgentBloc()),
        BlocProvider(create: (context) => PositionBloc()),
        BlocProvider(create: (context) => HealthBloc()),
        BlocProvider(
          create: (context) => SettingsBloc()..add(SettingsLoadRequested()),
        ),
      ],
      child: BlocBuilder<AuthBloc, AuthState>(
        builder: (context, authState) {
          return BlocBuilder<SettingsBloc, SettingsState>(
            builder: (context, settingsState) {
              final isDarkMode = settingsState is SettingsLoadedState
                  ? settingsState.settings.darkModeEnabled
                  : false;

              return MaterialApp.router(
                title: 'Porta',
                theme: ThemeData(
                  colorScheme: ColorScheme.fromSeed(
                    seedColor: Colors.blue,
                    brightness: isDarkMode ? Brightness.dark : Brightness.light,
                  ),
                  useMaterial3: true,
                ),
                routerConfig: _createRouter(authState),
              );
            },
          );
        },
      ),
    );
  }

  GoRouter _createRouter(AuthState authState) {
    return GoRouter(
      initialLocation: '/login',
      redirect: (context, state) {
        final isAuthenticated =
            authState is AuthAuthenticated || authState is AuthEmailNotVerified;
        final isAuthRoute =
            state.matchedLocation.startsWith('/auth') ||
            state.matchedLocation == '/login' ||
            state.matchedLocation == '/register';

        // If not authenticated and not on auth route, redirect to login
        if (!isAuthenticated && !isAuthRoute) {
          return '/login';
        }

        // If authenticated and on auth route, redirect to home
        if (isAuthenticated && isAuthRoute) {
          return '/';
        }

        return null; // No redirect needed
      },
      routes: [
        GoRoute(
          path: '/login',
          pageBuilder: (context, state) =>
              _buildPageWithTransition(context, state, const LoginScreen()),
        ),
        GoRoute(
          path: '/register',
          pageBuilder: (context, state) =>
              _buildPageWithTransition(context, state, const RegisterScreen()),
        ),
        ShellRoute(
          builder: (context, state, child) {
            return HomeScreen(child: child);
          },
          routes: [
            GoRoute(
              path: '/',
              pageBuilder: (context, state) => _buildPageWithTransition(
                context,
                state,
                const PortfolioScreen(),
                isShell: true,
              ),
            ),
            GoRoute(
              path: '/portfolio',
              pageBuilder: (context, state) => _buildPageWithTransition(
                context,
                state,
                const PortfolioScreen(),
                isShell: true,
              ),
            ),
            GoRoute(
              path: '/portfolio/edit',
              pageBuilder: (context, state) => _buildPageWithTransition(
                context,
                state,
                const PortfolioEditScreen(),
                isShell: true,
              ),
            ),
            GoRoute(
              path: '/agent',
              pageBuilder: (context, state) => _buildPageWithTransition(
                context,
                state,
                const AgentScreen(),
                isShell: true,
              ),
            ),
            GoRoute(
              path: '/position',
              pageBuilder: (context, state) => _buildPageWithTransition(
                context,
                state,
                const PositionListScreen(),
                isShell: true,
              ),
            ),
            GoRoute(
              path: '/position/add',
              pageBuilder: (context, state) => _buildPageWithTransition(
                context,
                state,
                const PositionManageScreen(),
                isShell: true,
              ),
            ),
            GoRoute(
              path: '/position/edit/:id',
              pageBuilder: (context, state) {
                final positionId = int.tryParse(
                  state.pathParameters['id'] ?? '',
                );
                return _buildPageWithTransition(
                  context,
                  state,
                  PositionManageScreen(positionId: positionId),
                  isShell: true,
                );
              },
            ),
            GoRoute(
              path: '/health',
              pageBuilder: (context, state) => _buildPageWithTransition(
                context,
                state,
                const HealthScreen(),
                isShell: true,
              ),
            ),
            GoRoute(
              path: '/settings',
              pageBuilder: (context, state) => _buildPageWithTransition(
                context,
                state,
                const SettingsScreen(),
                isShell: true,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Page<T> _buildPageWithTransition<T>(
    BuildContext context,
    GoRouterState state,
    Widget child, {
    bool isShell = false,
  }) {
    if (isShell) {
      // For shell routes, use no transition to avoid conflicts
      return NoTransitionPage<T>(key: state.pageKey, child: child);
    }

    return CustomTransitionPage<T>(
      key: state.pageKey,
      child: child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        const begin = Offset(1.0, 0.0);
        const end = Offset.zero;
        const curve = Curves.easeInOutCubic;

        var tween = Tween(
          begin: begin,
          end: end,
        ).chain(CurveTween(curve: curve));

        return SlideTransition(
          position: animation.drive(tween),
          child: FadeTransition(opacity: animation, child: child),
        );
      },
    );
  }
}

class CustomTransitionPage<T> extends Page<T> {
  final Widget child;
  final RouteTransitionsBuilder transitionsBuilder;

  const CustomTransitionPage({
    required this.child,
    required this.transitionsBuilder,
    super.key,
    super.name,
    super.arguments,
    super.restorationId,
  });

  @override
  Route<T> createRoute(BuildContext context) {
    return PageRouteBuilder<T>(
      settings: this,
      pageBuilder: (context, animation, secondaryAnimation) => child,
      transitionsBuilder: transitionsBuilder,
      transitionDuration: const Duration(milliseconds: 300),
      reverseTransitionDuration: const Duration(milliseconds: 300),
    );
  }
}

class NoTransitionPage<T> extends Page<T> {
  final Widget child;

  const NoTransitionPage({
    required this.child,
    super.key,
    super.name,
    super.arguments,
    super.restorationId,
  });

  @override
  Route<T> createRoute(BuildContext context) {
    return PageRouteBuilder<T>(
      settings: this,
      pageBuilder: (context, animation, secondaryAnimation) => child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) =>
          child,
      transitionDuration: Duration.zero,
      reverseTransitionDuration: Duration.zero,
    );
  }
}
