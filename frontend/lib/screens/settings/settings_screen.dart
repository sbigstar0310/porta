import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../bloc/settings/settings_bloc.dart';
import '../../bloc/settings/settings_event.dart';
import '../../bloc/settings/settings_state.dart';
import '../../bloc/auth/auth_bloc.dart';
import '../../bloc/auth/auth_event.dart';
import '../../bloc/auth/auth_state.dart';
import '../../constants/colors.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final TextEditingController _reportTimeController = TextEditingController();

  @override
  void dispose() {
    _reportTimeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark
          ? AppColors.darkBackground
          : AppColors.neutralGray50,
      body: BlocBuilder<SettingsBloc, SettingsState>(
        builder: (context, settingsState) {
          if (settingsState is SettingsLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (settingsState is SettingsError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: AppColors.error),
                  const SizedBox(height: 16),
                  Text(
                    settingsState.message,
                    style: TextStyle(color: AppColors.error, fontSize: 16),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: () => context.read<SettingsBloc>().add(
                      SettingsLoadRequested(),
                    ),
                    child: const Text('다시 시도'),
                  ),
                ],
              ),
            );
          }

          if (settingsState is SettingsLoadedState) {
            final settings = settingsState.settings;
            _reportTimeController.text = settings.reportTime;

            return CustomScrollView(
              physics: const BouncingScrollPhysics(),
              slivers: [
                // Modern header
                SliverToBoxAdapter(child: _buildModernHeader(context, isDark)),

                // User Info Section
                SliverToBoxAdapter(
                  child: BlocBuilder<AuthBloc, AuthState>(
                    builder: (context, authState) {
                      return _buildUserInfoSection(context, authState, isDark);
                    },
                  ),
                ),

                // App Settings Section
                SliverToBoxAdapter(
                  child: _buildAppSettingsSection(
                    context,
                    settings,
                    settingsState,
                    isDark,
                  ),
                ),

                // Report Settings Section
                SliverToBoxAdapter(
                  child: _buildReportSettingsSection(context, settings, isDark),
                ),

                // App Info Section
                SliverToBoxAdapter(
                  child: _buildAppInfoSection(context, isDark),
                ),

                // Bottom padding
                const SliverToBoxAdapter(child: SizedBox(height: 100)),
              ],
            );
          }

          return const SizedBox.shrink();
        },
      ),
    );
  }

  Widget _buildModernHeader(BuildContext context, bool isDark) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 60, 24, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  gradient: AppColors.primaryGradient,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.settings_outlined,
                  color: Colors.white,
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '설정',
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: isDark
                                ? Colors.white
                                : AppColors.neutralGray900,
                          ),
                    ),
                    Text(
                      '앱 환경설정 및 계정 관리',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: isDark
                            ? AppColors.neutralGray400
                            : AppColors.neutralGray600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildUserInfoSection(
    BuildContext context,
    AuthState authState,
    bool isDark,
  ) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark ? AppColors.neutralGray700 : AppColors.neutralGray200,
        ),
        boxShadow: [
          BoxShadow(
            color: isDark
                ? Colors.black.withOpacity(0.2)
                : AppColors.shadowLight,
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.info.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.person_outline,
                  color: AppColors.info,
                  size: 20,
                ),
              ),
              const SizedBox(width: 16),
              Text(
                '계정 정보',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: isDark ? Colors.white : AppColors.neutralGray900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Email info
          _buildModernListTile(
            context,
            Icons.email_outlined,
            '이메일',
            authState is AuthAuthenticated
                ? authState.user.email ?? '이메일 없음'
                : '로그인되지 않음',
            null,
            isDark,
          ),

          const SizedBox(height: 16),

          // Logout button
          _buildModernListTile(
            context,
            Icons.logout_outlined,
            '로그아웃',
            '계정에서 로그아웃합니다',
            () => _showLogoutDialog(context),
            isDark,
          ),

          const SizedBox(height: 16),

          // Delete account button
          _buildModernListTile(
            context,
            Icons.delete_forever_outlined,
            '회원 탈퇴',
            '계정을 영구적으로 삭제합니다',
            () => _showDeleteAccountDialog(context),
            isDark,
            isDestructive: true,
          ),
        ],
      ),
    );
  }

  Widget _buildAppSettingsSection(
    BuildContext context,
    dynamic settings,
    SettingsLoadedState settingsState,
    bool isDark,
  ) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark ? AppColors.neutralGray700 : AppColors.neutralGray200,
        ),
        boxShadow: [
          BoxShadow(
            color: isDark
                ? Colors.black.withOpacity(0.2)
                : AppColors.shadowLight,
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.secondaryIndigo.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.tune_outlined,
                  color: AppColors.secondaryIndigo,
                  size: 20,
                ),
              ),
              const SizedBox(width: 16),
              Text(
                '앱 설정',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: isDark ? Colors.white : AppColors.neutralGray900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Dark mode toggle
          _buildModernSwitchTile(
            context,
            Icons.dark_mode_outlined,
            '다크 모드',
            '어두운 테마 사용',
            settings.darkModeEnabled,
            (value) {
              context.read<SettingsBloc>().add(SettingsDarkModeToggled(value));
            },
            isDark,
          ),

          const SizedBox(height: 16),

          // Language setting
          _buildModernListTile(
            context,
            Icons.language_outlined,
            '언어',
            settingsState.getLanguageName(settings.language),
            () => _showLanguageDialog(context, settingsState),
            isDark,
          ),
        ],
      ),
    );
  }

  Widget _buildReportSettingsSection(
    BuildContext context,
    dynamic settings,
    bool isDark,
  ) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark ? AppColors.neutralGray700 : AppColors.neutralGray200,
        ),
        boxShadow: [
          BoxShadow(
            color: isDark
                ? Colors.black.withOpacity(0.2)
                : AppColors.shadowLight,
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.warning.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.report_outlined,
                  color: AppColors.warning,
                  size: 20,
                ),
              ),
              const SizedBox(width: 16),
              Text(
                '보고서 설정',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: isDark ? Colors.white : AppColors.neutralGray900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Report time setting
          _buildModernListTile(
            context,
            Icons.access_time_outlined,
            '보고서 시간',
            settings.reportTime == "09:00"
                ? '시간을 설정해주세요 (기본값: ${settings.reportTime})'
                : '매일 ${settings.reportTime}에 보고서 전송',
            () => _showTimePickerDialog(context),
            isDark,
          ),
        ],
      ),
    );
  }

  Widget _buildAppInfoSection(BuildContext context, bool isDark) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark ? AppColors.neutralGray700 : AppColors.neutralGray200,
        ),
        boxShadow: [
          BoxShadow(
            color: isDark
                ? Colors.black.withOpacity(0.2)
                : AppColors.shadowLight,
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.success.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.info_outline,
                  color: AppColors.success,
                  size: 20,
                ),
              ),
              const SizedBox(width: 16),
              Text(
                '앱 정보',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: isDark ? Colors.white : AppColors.neutralGray900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Version info
          _buildModernListTile(
            context,
            Icons.smartphone_outlined,
            '버전',
            '1.0.0',
            null,
            isDark,
          ),

          const SizedBox(height: 16),

          // Reset settings
          _buildModernListTile(
            context,
            Icons.restore_outlined,
            '설정 초기화',
            '모든 설정을 기본값으로 복원',
            () => _showResetDialog(context),
            isDark,
          ),
        ],
      ),
    );
  }

  Widget _buildModernListTile(
    BuildContext context,
    IconData icon,
    String title,
    String subtitle,
    VoidCallback? onTap,
    bool isDark, {
    bool isDestructive = false,
  }) {
    final color = isDestructive ? AppColors.error : null;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isDark
                ? AppColors.darkSurfaceVariant.withOpacity(0.3)
                : AppColors.neutralGray50,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              Icon(
                icon,
                color:
                    color ??
                    (isDark
                        ? AppColors.neutralGray400
                        : AppColors.neutralGray600),
                size: 20,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color:
                            color ??
                            (isDark ? Colors.white : AppColors.neutralGray900),
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: TextStyle(
                        color: isDark
                            ? AppColors.neutralGray400
                            : AppColors.neutralGray600,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
              if (onTap != null)
                Icon(
                  Icons.chevron_right,
                  color: isDark
                      ? AppColors.neutralGray500
                      : AppColors.neutralGray400,
                  size: 20,
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModernSwitchTile(
    BuildContext context,
    IconData icon,
    String title,
    String subtitle,
    bool value,
    ValueChanged<bool> onChanged,
    bool isDark,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark
            ? AppColors.darkSurfaceVariant.withOpacity(0.3)
            : AppColors.neutralGray50,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(
            icon,
            color: isDark ? AppColors.neutralGray400 : AppColors.neutralGray600,
            size: 20,
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: isDark ? Colors.white : AppColors.neutralGray900,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: TextStyle(
                    color: isDark
                        ? AppColors.neutralGray400
                        : AppColors.neutralGray600,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: AppColors.primaryBlue,
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('로그아웃'),
          content: const Text('로그아웃하시겠습니까?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('취소'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                context.read<AuthBloc>().add(AuthLogoutRequested());
              },
              child: const Text('로그아웃'),
            ),
          ],
        );
      },
    );
  }

  void _showLanguageDialog(
    BuildContext context,
    SettingsLoadedState settingsState,
  ) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('언어 선택'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: settingsState.availableLanguages.map((language) {
              return RadioListTile<String>(
                title: Text(settingsState.getLanguageName(language)),
                value: language,
                groupValue: settingsState.settings.language,
                onChanged: (value) {
                  if (value != null) {
                    context.read<SettingsBloc>().add(
                      SettingsLanguageChanged(value),
                    );
                    Navigator.of(context).pop();
                  }
                },
              );
            }).toList(),
          ),
        );
      },
    );
  }

  void _showTimePickerDialog(BuildContext context) async {
    // 현재 설정된 시간을 초기값으로 사용, 기본값(09:00)인 경우 현재 시간 사용
    final settingsState = context.read<SettingsBloc>().state;
    TimeOfDay initialTime = TimeOfDay.now();

    if (settingsState is SettingsLoadedState) {
      final reportTime = settingsState.settings.reportTime;
      // 기본값(09:00)이 아닌 경우에만 설정된 시간 사용
      if (reportTime != "09:00") {
        final timeParts = reportTime.split(':');
        final hour = int.parse(timeParts[0]);
        final minute = int.parse(timeParts[1]);
        initialTime = TimeOfDay(hour: hour, minute: minute);
      }
      // 기본값인 경우 현재 시간을 초기값으로 사용 (이미 TimeOfDay.now()로 설정됨)
    }

    final TimeOfDay? pickedTime = await showTimePicker(
      context: context,
      initialTime: initialTime,
    );

    if (pickedTime != null) {
      final timeString =
          '${pickedTime.hour.toString().padLeft(2, '0')}:${pickedTime.minute.toString().padLeft(2, '0')}';
      if (context.mounted) {
        context.read<SettingsBloc>().add(SettingsReportTimeUpdated(timeString));
      }
    }
  }

  void _showResetDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('설정 초기화'),
          content: const Text('모든 설정을 기본값으로 복원하시겠습니까?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('취소'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                context.read<SettingsBloc>().add(SettingsResetToDefaults());
              },
              child: const Text('초기화'),
            ),
          ],
        );
      },
    );
  }

  void _showDeleteAccountDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return BlocListener<AuthBloc, AuthState>(
          listener: (context, state) {
            if (state is AuthUnauthenticated) {
              Navigator.of(context).pop(); // 다이얼로그 닫기
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('회원 탈퇴가 완료되었습니다'),
                  backgroundColor: Colors.green,
                ),
              );
            } else if (state is AuthError) {
              Navigator.of(context).pop(); // 다이얼로그 닫기
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(state.message),
                  backgroundColor: Colors.red,
                ),
              );
            }
          },
          child: AlertDialog(
            title: Row(
              children: [
                Icon(Icons.warning, color: Theme.of(context).colorScheme.error),
                const SizedBox(width: 8),
                const Text('회원 탈퇴'),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '정말로 회원 탈퇴를 하시겠습니까?',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.errorContainer,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '주의사항:',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).colorScheme.onErrorContainer,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '• 모든 포트폴리오 데이터가 삭제됩니다\n• 계정 복구가 불가능합니다\n• 이 작업은 되돌릴 수 없습니다',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onErrorContainer,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('취소'),
              ),
              BlocBuilder<AuthBloc, AuthState>(
                builder: (context, state) {
                  return TextButton(
                    onPressed: state is AuthLoading
                        ? null
                        : () {
                            context.read<AuthBloc>().add(AuthDeleteRequested());
                          },
                    style: TextButton.styleFrom(
                      foregroundColor: Theme.of(context).colorScheme.error,
                    ),
                    child: state is AuthLoading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('탈퇴하기'),
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }
}
