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
import 'constants/colors.dart';
import 'services/storage_service.dart';
import 'services/dio_client.dart';
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
  late AuthBloc _authBloc;

  @override
  void initState() {
    super.initState();
    _initializeServices();
  }

  Future<void> _initializeServices() async {
    await StorageService.init();
  }

  void _setupEmailVerificationCallback(AuthBloc authBloc) {
    _authBloc = authBloc;
    // DioClient의 이메일 인증 성공 콜백 설정
    DioClient.onEmailVerificationSuccess = (message) {
      _authBloc.add(AuthEmailVerificationSuccess(message: message));
    };
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (context) {
            final authBloc = AuthBloc()..add(AuthInitialized());
            _setupEmailVerificationCallback(authBloc);
            return authBloc;
          },
        ),
        BlocProvider(create: (context) => PortfolioBloc()),
        BlocProvider(create: (context) => AgentBloc()),
        BlocProvider(create: (context) => PositionBloc()),
        BlocProvider(create: (context) => HealthBloc()),
        BlocProvider(
          create: (context) => SettingsBloc()..add(SettingsLoadRequested()),
        ),
      ],
      child: BlocBuilder<SettingsBloc, SettingsState>(
        buildWhen: (previous, current) {
          // 다크모드 설정이 실제로 변경되었을 때만 리빌드
          if (previous is SettingsLoadedState &&
              current is SettingsLoadedState) {
            return previous.settings.darkModeEnabled !=
                current.settings.darkModeEnabled;
          }
          // 초기 로딩 완료 시에는 리빌드
          return current is SettingsLoadedState &&
              previous is! SettingsLoadedState;
        },
        builder: (context, settingsState) {
          final isDarkMode = settingsState is SettingsLoadedState
              ? settingsState.settings.darkModeEnabled
              : false;

          return BlocBuilder<AuthBloc, AuthState>(
            builder: (context, authState) {
              // 인증 상태가 변경될 때마다 라우터 재생성 (로그인/로그아웃 처리를 위해)
              final router = _createRouter(authState);

              return MaterialApp.router(
                title: 'Porta',
                theme: _buildLightTheme(),
                darkTheme: _buildDarkTheme(),
                themeMode: isDarkMode ? ThemeMode.dark : ThemeMode.light,
                routerConfig: router,
              );
            },
          );
        },
      ),
    );
  }

  ThemeData _buildLightTheme() {
    return ThemeData(
      useMaterial3: true,
      colorScheme: AppColors.lightColorScheme,
      fontFamily: 'Inter', // 모던한 폰트
      // AppBar 테마
      appBarTheme: const AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 1,
        backgroundColor: Colors.transparent,
        foregroundColor: AppColors.neutralGray900,
        titleTextStyle: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: AppColors.neutralGray900,
        ),
      ),

      // Card 테마
      cardTheme: CardThemeData(
        elevation: 2,
        shadowColor: AppColors.shadowLight,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        color: Colors.white,
      ),

      // ElevatedButton 테마
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 2,
          shadowColor: AppColors.shadowMedium,
          backgroundColor: AppColors.primaryBlue,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),

      // OutlinedButton 테마
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primaryBlue,
          side: const BorderSide(color: AppColors.primaryBlue, width: 1.5),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),

      // TextButton 테마
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primaryBlue,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
        ),
      ),

      // InputDecoration 테마
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.neutralGray50,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.neutralGray300),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.neutralGray300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.primaryBlue, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.error),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 16,
        ),
      ),

      // FloatingActionButton 테마
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: AppColors.primaryBlue,
        foregroundColor: Colors.white,
        elevation: 4,
        shape: CircleBorder(),
      ),

      // BottomNavigationBar 테마
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        selectedItemColor: AppColors.primaryBlue,
        unselectedItemColor: AppColors.neutralGray500,
        elevation: 8,
        type: BottomNavigationBarType.fixed,
      ),
    );
  }

  ThemeData _buildDarkTheme() {
    return ThemeData(
      useMaterial3: true,
      colorScheme: AppColors.darkColorScheme,
      fontFamily: 'Inter',

      // AppBar 테마
      appBarTheme: const AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 1,
        backgroundColor: Colors.transparent,
        foregroundColor: AppColors.neutralGray100,
        titleTextStyle: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: AppColors.neutralGray100,
        ),
      ),

      // Card 테마
      cardTheme: CardThemeData(
        elevation: 4,
        shadowColor: Colors.black.withOpacity(0.3),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        color: AppColors.darkSurface,
      ),

      // ElevatedButton 테마
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 4,
          shadowColor: Colors.black.withOpacity(0.3),
          backgroundColor: AppColors.primaryBlueAccent,
          foregroundColor: AppColors.darkBackground,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),

      // OutlinedButton 테마
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primaryBlueAccent,
          side: const BorderSide(
            color: AppColors.primaryBlueAccent,
            width: 1.5,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),

      // TextButton 테마
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primaryBlueAccent,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
        ),
      ),

      // InputDecoration 테마
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.darkSurfaceVariant,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.neutralGray600),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.neutralGray600),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(
            color: AppColors.primaryBlueAccent,
            width: 2,
          ),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.errorLight),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 16,
        ),
      ),

      // FloatingActionButton 테마
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: AppColors.primaryBlueAccent,
        foregroundColor: AppColors.darkBackground,
        elevation: 6,
        shape: CircleBorder(),
      ),

      // BottomNavigationBar 테마
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.darkSurface,
        selectedItemColor: AppColors.primaryBlueAccent,
        unselectedItemColor: AppColors.neutralGray400,
        elevation: 8,
        type: BottomNavigationBarType.fixed,
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
