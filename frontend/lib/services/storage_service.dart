import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import '../models/settings.dart';

class StorageService {
  static const _secureStorage = FlutterSecureStorage();
  static SharedPreferences? _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // Secure storage for sensitive data
  static Future<void> saveAuthToken(String token) async {
    await _secureStorage.write(key: 'auth_token', value: token);
  }

  static Future<String?> getAuthToken() async {
    return await _secureStorage.read(key: 'auth_token');
  }

  static Future<void> deleteAuthToken() async {
    await _secureStorage.delete(key: 'auth_token');
  }

  static Future<void> saveRefreshToken(String token) async {
    await _secureStorage.write(key: 'refresh_token', value: token);
  }

  static Future<String?> getRefreshToken() async {
    return await _secureStorage.read(key: 'refresh_token');
  }

  static Future<void> deleteRefreshToken() async {
    await _secureStorage.delete(key: 'refresh_token');
  }

  // App settings
  static Future<void> saveSettings(AppSettings settings) async {
    await _prefs?.setString('app_settings', json.encode(settings.toJson()));
  }

  static Future<AppSettings> getSettings() async {
    final settingsJson = _prefs?.getString('app_settings');
    if (settingsJson != null) {
      return AppSettings.fromJson(json.decode(settingsJson));
    }
    return AppSettings(); // Default settings
  }

  // User data cache
  static Future<void> saveUserData(String userData) async {
    await _prefs?.setString('user_data', userData);
  }

  static Future<String?> getUserData() async {
    return _prefs?.getString('user_data');
  }

  static Future<void> deleteUserData() async {
    await _prefs?.remove('user_data');
  }

  // First launch flag
  static Future<bool> isFirstLaunch() async {
    return _prefs?.getBool('first_launch') ?? true;
  }

  static Future<void> setFirstLaunchComplete() async {
    await _prefs?.setBool('first_launch', false);
  }

  // Clear all data
  static Future<void> clearAll() async {
    await _secureStorage.deleteAll();
    await _prefs?.clear();
  }
}
