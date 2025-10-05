class AppSettings {
  final bool darkModeEnabled;
  final String reportTime; // "09:00" format
  final String language;

  AppSettings({
    this.darkModeEnabled = false,
    this.reportTime = "09:00",
    this.language = "ko",
  });

  factory AppSettings.fromJson(Map<String, dynamic> json) {
    return AppSettings(
      darkModeEnabled: json['dark_mode_enabled'] as bool? ?? false,
      reportTime: json['report_time'] as String? ?? "09:00",
      language: json['language'] as String? ?? "ko",
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'dark_mode_enabled': darkModeEnabled,
      'report_time': reportTime,
      'language': language,
    };
  }

  AppSettings copyWith({
    bool? darkModeEnabled,
    String? reportTime,
    String? language,
  }) {
    return AppSettings(
      darkModeEnabled: darkModeEnabled ?? this.darkModeEnabled,
      reportTime: reportTime ?? this.reportTime,
      language: language ?? this.language,
    );
  }
}
