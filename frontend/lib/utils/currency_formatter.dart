import 'package:intl/intl.dart';

class CurrencyFormatter {
  /// 통화 코드에 따른 심볼 매핑
  static const Map<String, String> _currencySymbols = {
    'USD': '\$',
    'KRW': '₩',
    'EUR': '€',
    'JPY': '¥',
    'GBP': '£',
    'CNY': '¥',
    'CAD': 'C\$',
    'AUD': 'A\$',
    'CHF': 'CHF',
    'HKD': 'HK\$',
    'SGD': 'S\$',
  };

  /// 통화 코드에 따른 기본 로케일 매핑
  static const Map<String, String> _currencyLocales = {
    'USD': 'en_US',
    'KRW': 'ko_KR',
    'EUR': 'en_US',
    'JPY': 'ja_JP',
    'GBP': 'en_GB',
    'CNY': 'zh_CN',
    'CAD': 'en_CA',
    'AUD': 'en_AU',
    'CHF': 'en_CH',
    'HKD': 'en_HK',
    'SGD': 'en_SG',
  };

  /// 통화별 기본 소수점 자릿수 반환
  static int _getDecimalDigits(String currencyCode) {
    switch (currencyCode.toUpperCase()) {
      case 'KRW':
      case 'JPY':
        return 0; // 원, 엔은 소수점 없음
      default:
        return 2; // 기본 2자리
    }
  }

  /// 통화 포맷터 생성
  static NumberFormat createFormatter(String currencyCode) {
    final normalizedCode = currencyCode.toUpperCase();
    final locale = _currencyLocales[normalizedCode] ?? 'en_US';
    final symbol = _currencySymbols[normalizedCode] ?? normalizedCode;
    final decimalDigits = _getDecimalDigits(normalizedCode);

    return NumberFormat.currency(
      locale: locale,
      symbol: symbol,
      decimalDigits: decimalDigits,
    );
  }

  /// 간단한 통화 포맷팅
  static String format(double amount, String currencyCode) {
    final formatter = createFormatter(currencyCode);
    return formatter.format(amount);
  }

  /// 통화 심볼만 반환
  static String getSymbol(String currencyCode) {
    return _currencySymbols[currencyCode.toUpperCase()] ?? currencyCode;
  }

  /// 지원되는 통화 목록 반환
  static List<String> getSupportedCurrencies() {
    return _currencySymbols.keys.toList();
  }

  /// 통화 코드의 전체 이름 반환
  static String getCurrencyName(String currencyCode) {
    switch (currencyCode.toUpperCase()) {
      case 'USD':
        return '미국 달러';
      case 'KRW':
        return '한국 원';
      case 'EUR':
        return '유로';
      case 'JPY':
        return '일본 엔';
      case 'GBP':
        return '영국 파운드';
      case 'CNY':
        return '중국 위안';
      case 'CAD':
        return '캐나다 달러';
      case 'AUD':
        return '호주 달러';
      case 'CHF':
        return '스위스 프랑';
      case 'HKD':
        return '홍콩 달러';
      case 'SGD':
        return '싱가포르 달러';
      default:
        return currencyCode.toUpperCase();
    }
  }
}
