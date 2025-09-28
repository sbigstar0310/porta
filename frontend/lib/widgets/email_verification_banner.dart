import 'package:flutter/material.dart';
import 'dart:async';
import '../services/api_service.dart';
import '../models/user.dart';

class EmailVerificationBanner extends StatefulWidget {
  final User user;

  const EmailVerificationBanner({super.key, required this.user});

  @override
  State<EmailVerificationBanner> createState() =>
      _EmailVerificationBannerState();
}

class _EmailVerificationBannerState extends State<EmailVerificationBanner> {
  bool _isResendingEmail = false;
  bool _canResendEmail = true;
  int _resendCountdown = 0;
  Timer? _resendTimer;
  final ApiService _apiService = ApiService();

  @override
  void dispose() {
    _resendTimer?.cancel();
    super.dispose();
  }

  Future<void> _handleResendEmail() async {
    if (!_canResendEmail || _isResendingEmail || widget.user.email == null)
      return;

    setState(() {
      _isResendingEmail = true;
    });

    try {
      await _apiService.resendVerificationEmail(widget.user.email!);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('인증 이메일이 발송되었습니다.'),
            backgroundColor: Colors.green,
          ),
        );
        _startResendCooldown();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('이메일 발송 실패: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isResendingEmail = false;
        });
      }
    }
  }

  void _startResendCooldown() {
    setState(() {
      _canResendEmail = false;
      _resendCountdown = 60;
    });

    _resendTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() {
        _resendCountdown--;
      });

      if (_resendCountdown <= 0) {
        timer.cancel();
        setState(() {
          _canResendEmail = true;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.orange.withOpacity(0.1),
            Colors.deepOrange.withOpacity(0.1),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.orange.withOpacity(0.3), width: 1),
      ),
      child: Row(
        children: [
          // 아이콘
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.orange.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              Icons.email_outlined,
              color: Colors.orange.shade700,
              size: 24,
            ),
          ),
          const SizedBox(width: 16),

          // 메시지 영역
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '이메일 인증이 필요합니다',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Colors.orange.shade800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${widget.user.email}로 발송된 인증 링크를 클릭해주세요.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.orange.shade700,
                  ),
                ),
              ],
            ),
          ),

          // 버튼 영역
          const SizedBox(width: 16),
          OutlinedButton.icon(
            onPressed: _canResendEmail && !_isResendingEmail
                ? _handleResendEmail
                : null,
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.orange.shade700,
              side: BorderSide(color: Colors.orange.shade300),
              backgroundColor: Colors.white.withOpacity(0.8),
            ),
            icon: _isResendingEmail
                ? SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        Colors.orange.shade700,
                      ),
                    ),
                  )
                : const Icon(Icons.refresh, size: 16),
            label: Text(
              _canResendEmail ? '재발송' : '${_resendCountdown}초',
              style: const TextStyle(fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
