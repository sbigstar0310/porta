class AppSettings {
  final bool notificationsEnabled;
  final bool darkModeEnabled;
  final String reportTime; // "09:00" format
  final bool weekendReports;
  final String language;

  AppSettings({
    this.notificationsEnabled = true,
    this.darkModeEnabled = false,
    this.reportTime = "09:00",
    this.weekendReports = false,
    this.language = "ko",
  });

  factory AppSettings.fromJson(Map<String, dynamic> json) {
    return AppSettings(
      notificationsEnabled: json['notifications_enabled'] as bool? ?? true,
      darkModeEnabled: json['dark_mode_enabled'] as bool? ?? false,
      reportTime: json['report_time'] as String? ?? "09:00",
      weekendReports: json['weekend_reports'] as bool? ?? false,
      language: json['language'] as String? ?? "ko",
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'notifications_enabled': notificationsEnabled,
      'dark_mode_enabled': darkModeEnabled,
      'report_time': reportTime,
      'weekend_reports': weekendReports,
      'language': language,
    };
  }

  AppSettings copyWith({
    bool? notificationsEnabled,
    bool? darkModeEnabled,
    String? reportTime,
    bool? weekendReports,
    String? language,
  }) {
    return AppSettings(
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      darkModeEnabled: darkModeEnabled ?? this.darkModeEnabled,
      reportTime: reportTime ?? this.reportTime,
      weekendReports: weekendReports ?? this.weekendReports,
      language: language ?? this.language,
    );
  }
}
