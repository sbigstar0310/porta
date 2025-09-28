class User {
  final int id;
  final String? email;
  final String timezone;
  final String language;
  final bool emailVerified;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime lastLogin;

  // 인증 토큰들 (로그인 응답에서만 포함)
  final String? accessToken;
  final String? refreshToken;
  final String? tokenType;
  final int? expiresIn;

  User({
    required this.id,
    this.email,
    required this.timezone,
    required this.language,
    required this.emailVerified,
    required this.createdAt,
    required this.updatedAt,
    required this.lastLogin,
    this.accessToken,
    this.refreshToken,
    this.tokenType,
    this.expiresIn,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      email: json['email'] as String?,
      timezone: json['timezone'] as String,
      language: json['language'] as String,
      emailVerified: json['email_verified'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      lastLogin: DateTime.parse(json['last_login'] as String),
      accessToken: json['access_token'] as String?,
      refreshToken: json['refresh_token'] as String?,
      tokenType: json['token_type'] as String?,
      expiresIn: json['expires_in'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {
      'id': id,
      'email': email,
      'timezone': timezone,
      'language': language,
      'email_verified': emailVerified,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'last_login': lastLogin.toIso8601String(),
    };

    // 토큰 정보는 null이 아닐 때만 포함
    if (accessToken != null) data['access_token'] = accessToken;
    if (refreshToken != null) data['refresh_token'] = refreshToken;
    if (tokenType != null) data['token_type'] = tokenType;
    if (expiresIn != null) data['expires_in'] = expiresIn;

    return data;
  }

  User copyWith({
    int? id,
    String? email,
    String? timezone,
    String? language,
    bool? emailVerified,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? lastLogin,
    String? accessToken,
    String? refreshToken,
    String? tokenType,
    int? expiresIn,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      timezone: timezone ?? this.timezone,
      language: language ?? this.language,
      emailVerified: emailVerified ?? this.emailVerified,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      lastLogin: lastLogin ?? this.lastLogin,
      accessToken: accessToken ?? this.accessToken,
      refreshToken: refreshToken ?? this.refreshToken,
      tokenType: tokenType ?? this.tokenType,
      expiresIn: expiresIn ?? this.expiresIn,
    );
  }
}
