import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../bloc/settings/settings_bloc.dart';
import '../../bloc/settings/settings_event.dart';
import '../../bloc/settings/settings_state.dart';
import '../../bloc/auth/auth_bloc.dart';
import '../../bloc/auth/auth_event.dart';
import '../../bloc/auth/auth_state.dart';

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
    return BlocBuilder<SettingsBloc, SettingsState>(
      builder: (context, settingsState) {
        if (settingsState is SettingsLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        if (settingsState is SettingsError) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  settingsState.message,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () =>
                      context.read<SettingsBloc>().add(SettingsLoadRequested()),
                  child: const Text('다시 시도'),
                ),
              ],
            ),
          );
        }

        if (settingsState is SettingsLoadedState) {
          final settings = settingsState.settings;
          _reportTimeController.text = settings.reportTime;

          return ListView(
            children: [
              // User Info Section
              BlocBuilder<AuthBloc, AuthState>(
                builder: (context, authState) {
                  return Card(
                    margin: const EdgeInsets.all(16),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '계정 정보',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 16),
                          ListTile(
                            leading: const Icon(Icons.person),
                            title: const Text('이메일'),
                            subtitle: Text(
                              authState is AuthAuthenticated
                                  ? authState.user.email ?? '이메일 없음'
                                  : '로그인되지 않음',
                            ),
                          ),
                          ListTile(
                            leading: const Icon(Icons.logout),
                            title: const Text('로그아웃'),
                            onTap: () => _showLogoutDialog(context),
                          ),
                          const Divider(),
                          ListTile(
                            leading: Icon(
                              Icons.delete_forever,
                              color: Theme.of(context).colorScheme.error,
                            ),
                            title: Text(
                              '회원 탈퇴',
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.error,
                              ),
                            ),
                            subtitle: const Text('계정을 영구적으로 삭제합니다'),
                            onTap: () => _showDeleteAccountDialog(context),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),

              // App Settings Section
              Card(
                margin: const EdgeInsets.all(16),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '앱 설정',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      SwitchListTile(
                        title: const Text('알림'),
                        subtitle: const Text('푸시 알림 받기'),
                        value: settings.notificationsEnabled,
                        onChanged: (value) {
                          context.read<SettingsBloc>().add(
                            SettingsNotificationsToggled(value),
                          );
                        },
                      ),
                      SwitchListTile(
                        title: const Text('다크 모드'),
                        subtitle: const Text('어두운 테마 사용'),
                        value: settings.darkModeEnabled,
                        onChanged: (value) {
                          context.read<SettingsBloc>().add(
                            SettingsDarkModeToggled(value),
                          );
                        },
                      ),
                      ListTile(
                        title: const Text('언어'),
                        subtitle: Text(
                          settingsState.getLanguageName(settings.language),
                        ),
                        trailing: const Icon(Icons.arrow_forward_ios),
                        onTap: () =>
                            _showLanguageDialog(context, settingsState),
                      ),
                    ],
                  ),
                ),
              ),

              // Report Settings Section
              Card(
                margin: const EdgeInsets.all(16),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '보고서 설정',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      ListTile(
                        title: const Text('보고서 시간'),
                        subtitle: Text('매일 ${settings.reportTime}에 보고서 전송'),
                        trailing: const Icon(Icons.access_time),
                        onTap: () => _showTimePickerDialog(context),
                      ),
                      SwitchListTile(
                        title: const Text('주말 보고서'),
                        subtitle: const Text('주말에도 보고서 받기'),
                        value: settings.weekendReports,
                        onChanged: (value) {
                          context.read<SettingsBloc>().add(
                            SettingsWeekendReportsToggled(value),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ),

              // App Info Section
              Card(
                margin: const EdgeInsets.all(16),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '앱 정보',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      const ListTile(
                        title: Text('버전'),
                        subtitle: Text('1.0.0'),
                      ),
                      ListTile(
                        title: const Text('설정 초기화'),
                        subtitle: const Text('모든 설정을 기본값으로 복원'),
                        trailing: const Icon(Icons.restore),
                        onTap: () => _showResetDialog(context),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        }

        return const SizedBox.shrink();
      },
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
    final currentTime = TimeOfDay.now();
    final TimeOfDay? pickedTime = await showTimePicker(
      context: context,
      initialTime: currentTime,
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
