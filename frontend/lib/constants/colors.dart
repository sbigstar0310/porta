import 'package:flutter/material.dart';

/// Porta 앱의 색상 시스템
/// 전문적이고 미래지향적인 퀀트 스타트업 테마
class AppColors {
  // Private constructor to prevent instantiation
  AppColors._();

  // Primary Blue Colors (메인 파란색 계열)
  static const Color primaryBlue = Color(0xFF1E3A8A); // 진한 파란색
  static const Color primaryBlueLight = Color(0xFF3B82F6); // 밝은 파란색
  static const Color primaryBlueDark = Color(0xFF1E40AF); // 더 진한 파란색
  static const Color primaryBlueAccent = Color(0xFF60A5FA); // 액센트 파란색

  // Secondary Colors (보조 색상)
  static const Color secondaryIndigo = Color(0xFF4F46E5); // 인디고
  static const Color secondaryPurple = Color(0xFF7C3AED); // 보라색
  static const Color secondaryCyan = Color(0xFF06B6D4); // 시안

  // Neutral Colors (중성 색상)
  static const Color neutralGray50 = Color(0xFFF9FAFB);
  static const Color neutralGray100 = Color(0xFFF3F4F6);
  static const Color neutralGray200 = Color(0xFFE5E7EB);
  static const Color neutralGray300 = Color(0xFFD1D5DB);
  static const Color neutralGray400 = Color(0xFF9CA3AF);
  static const Color neutralGray500 = Color(0xFF6B7280);
  static const Color neutralGray600 = Color(0xFF4B5563);
  static const Color neutralGray700 = Color(0xFF374151);
  static const Color neutralGray800 = Color(0xFF1F2937);
  static const Color neutralGray900 = Color(0xFF111827);

  // Dark Theme Colors
  static const Color darkBackground = Color(0xFF0F172A); // 매우 어두운 배경
  static const Color darkSurface = Color(0xFF1E293B); // 어두운 서페이스
  static const Color darkSurfaceVariant = Color(0xFF334155); // 서페이스 변형

  // Success Colors (성공/수익)
  static const Color success = Color(0xFF10B981);
  static const Color successLight = Color(0xFF34D399);
  static const Color successDark = Color(0xFF059669);
  static const Color successBackground = Color(0xFFECFDF5);

  // Error Colors (에러/손실)
  static const Color error = Color(0xFFEF4444);
  static const Color errorLight = Color(0xFFF87171);
  static const Color errorDark = Color(0xFFDC2626);
  static const Color errorBackground = Color(0xFFFEF2F2);

  // Warning Colors (경고)
  static const Color warning = Color(0xFFF59E0B);
  static const Color warningLight = Color(0xFFFBBF24);
  static const Color warningDark = Color(0xFFD97706);
  static const Color warningBackground = Color(0xFFFFFBEB);

  // Info Colors (정보)
  static const Color info = Color(0xFF3B82F6);
  static const Color infoLight = Color(0xFF60A5FA);
  static const Color infoDark = Color(0xFF2563EB);
  static const Color infoBackground = Color(0xFFEFF6FF);

  // Gradient Colors
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primaryBlue, primaryBlueLight],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient accentGradient = LinearGradient(
    colors: [secondaryIndigo, secondaryPurple],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient successGradient = LinearGradient(
    colors: [success, successLight],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient errorGradient = LinearGradient(
    colors: [error, errorLight],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Glass morphism colors
  static Color glassMorphismBackground = Colors.white.withOpacity(0.1);
  static Color glassMorphismBorder = Colors.white.withOpacity(0.2);

  // Shadow colors
  static Color shadowLight = Colors.black.withOpacity(0.1);
  static Color shadowMedium = Colors.black.withOpacity(0.15);
  static Color shadowHeavy = Colors.black.withOpacity(0.25);

  // Light Theme ColorScheme
  static const ColorScheme lightColorScheme = ColorScheme(
    brightness: Brightness.light,
    primary: primaryBlue,
    onPrimary: Colors.white,
    primaryContainer: Color(0xFFDEE7FF),
    onPrimaryContainer: Color(0xFF001A41),
    secondary: secondaryIndigo,
    onSecondary: Colors.white,
    secondaryContainer: Color(0xFFE0E7FF),
    onSecondaryContainer: Color(0xFF1E1B3A),
    tertiary: secondaryCyan,
    onTertiary: Colors.white,
    tertiaryContainer: Color(0xFFCCF7FE),
    onTertiaryContainer: Color(0xFF002022),
    error: error,
    onError: Colors.white,
    errorContainer: errorBackground,
    onErrorContainer: Color(0xFF410002),
    background: Colors.white,
    onBackground: neutralGray900,
    surface: neutralGray50,
    onSurface: neutralGray900,
    surfaceVariant: neutralGray100,
    onSurfaceVariant: neutralGray700,
    outline: neutralGray300,
    outlineVariant: neutralGray200,
    shadow: Colors.black,
    scrim: Colors.black,
    inverseSurface: neutralGray800,
    onInverseSurface: neutralGray100,
    inversePrimary: primaryBlueAccent,
  );

  // Dark Theme ColorScheme
  static const ColorScheme darkColorScheme = ColorScheme(
    brightness: Brightness.dark,
    primary: primaryBlueAccent,
    onPrimary: Color(0xFF001A41),
    primaryContainer: Color(0xFF002C71),
    onPrimaryContainer: Color(0xFFDEE7FF),
    secondary: Color(0xFFC4C6FF),
    onSecondary: Color(0xFF2D2D4F),
    secondaryContainer: Color(0xFF434366),
    onSecondaryContainer: Color(0xFFE0E7FF),
    tertiary: Color(0xFF4FD1C7),
    onTertiary: Color(0xFF003A37),
    tertiaryContainer: Color(0xFF005450),
    onTertiaryContainer: Color(0xFFCCF7FE),
    error: errorLight,
    onError: Color(0xFF410002),
    errorContainer: Color(0xFF93000A),
    onErrorContainer: Color(0xFFFFDAD6),
    background: darkBackground,
    onBackground: neutralGray100,
    surface: darkSurface,
    onSurface: neutralGray100,
    surfaceVariant: darkSurfaceVariant,
    onSurfaceVariant: neutralGray300,
    outline: neutralGray500,
    outlineVariant: neutralGray600,
    shadow: Colors.black,
    scrim: Colors.black,
    inverseSurface: neutralGray100,
    onInverseSurface: neutralGray800,
    inversePrimary: primaryBlue,
  );
}

/// 테마별 색상 확장
extension AppColorsExtension on ColorScheme {
  // 수익/손실 색상
  Color get profit => AppColors.success;
  Color get loss => AppColors.error;
  Color get profitBackground => AppColors.successBackground;
  Color get lossBackground => AppColors.errorBackground;

  // 카드 색상
  Color get cardBackground =>
      brightness == Brightness.light ? Colors.white : AppColors.darkSurface;

  Color get cardBorder => brightness == Brightness.light
      ? AppColors.neutralGray200
      : AppColors.neutralGray600;

  // 그라데이션 색상
  LinearGradient get primaryGradient => brightness == Brightness.light
      ? AppColors.primaryGradient
      : const LinearGradient(
          colors: [AppColors.primaryBlueAccent, AppColors.secondaryIndigo],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        );

  // 글래스모피즘 색상
  Color get glassMorphismBackground => brightness == Brightness.light
      ? Colors.white.withOpacity(0.7)
      : Colors.white.withOpacity(0.1);

  Color get glassMorphismBorder => brightness == Brightness.light
      ? Colors.white.withOpacity(0.3)
      : Colors.white.withOpacity(0.2);
}
