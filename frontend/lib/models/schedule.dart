class Schedule {
  final int id;
  final int userId;
  final int hour;
  final int minute;
  final String timezone;
  final bool enabled;

  Schedule({
    required this.id,
    required this.userId,
    required this.hour,
    required this.minute,
    required this.timezone,
    required this.enabled,
  });

  factory Schedule.fromJson(Map<String, dynamic> json) {
    return Schedule(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      hour: json['hour'] as int,
      minute: json['minute'] as int,
      timezone: json['timezone'] as String,
      enabled: json['enabled'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'hour': hour,
      'minute': minute,
      'timezone': timezone,
      'enabled': enabled,
    };
  }

  /// Schedule 시간을 "HH:mm" 형식으로 반환
  String get timeString {
    return '${hour.toString().padLeft(2, '0')}:${minute.toString().padLeft(2, '0')}';
  }

  Schedule copyWith({
    int? id,
    int? userId,
    int? hour,
    int? minute,
    String? timezone,
    bool? enabled,
  }) {
    return Schedule(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      hour: hour ?? this.hour,
      minute: minute ?? this.minute,
      timezone: timezone ?? this.timezone,
      enabled: enabled ?? this.enabled,
    );
  }
}
