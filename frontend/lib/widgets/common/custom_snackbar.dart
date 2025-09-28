import 'package:flutter/material.dart';

class CustomSnackBar {
  static void show(
    BuildContext context, {
    required String message,
    Color? backgroundColor,
    Color? textColor,
    IconData? icon,
    Duration duration = const Duration(seconds: 3),
    bool isError = false,
  }) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    // Remove any existing snackbars
    ScaffoldMessenger.of(context).clearSnackBars();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: _CustomSnackBarContent(
          message: message,
          icon:
              icon ??
              (isError ? Icons.error_outline : Icons.check_circle_outline),
          textColor:
              textColor ??
              (isError
                  ? colorScheme.onErrorContainer
                  : colorScheme.onPrimaryContainer),
          isError: isError,
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        duration: duration,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.only(bottom: 80, left: 16, right: 16),
      ),
    );
  }

  static void showSuccess(
    BuildContext context, {
    required String message,
    Duration duration = const Duration(seconds: 3),
  }) {
    show(
      context,
      message: message,
      icon: Icons.check_circle_outline,
      duration: duration,
      isError: false,
    );
  }

  static void showError(
    BuildContext context, {
    required String message,
    Duration duration = const Duration(seconds: 4),
  }) {
    show(
      context,
      message: message,
      icon: Icons.error_outline,
      duration: duration,
      isError: true,
    );
  }

  static void showInfo(
    BuildContext context, {
    required String message,
    Duration duration = const Duration(seconds: 3),
  }) {
    show(
      context,
      message: message,
      icon: Icons.info_outline,
      duration: duration,
      isError: false,
    );
  }
}

class _CustomSnackBarContent extends StatelessWidget {
  final String message;
  final IconData icon;
  final Color textColor;
  final bool isError;

  const _CustomSnackBarContent({
    required this.message,
    required this.icon,
    required this.textColor,
    this.isError = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    Color backgroundColor;
    Color iconColor;
    Color containerColor;

    if (isError) {
      backgroundColor = colorScheme.errorContainer;
      iconColor = colorScheme.error;
      containerColor = colorScheme.error.withOpacity(0.1);
    } else if (icon == Icons.check_circle_outline) {
      // Success case
      backgroundColor = Colors.green.shade50;
      iconColor = Colors.green.shade700;
      containerColor = Colors.green.withOpacity(0.1);
    } else {
      // Info case
      backgroundColor = colorScheme.primaryContainer;
      iconColor = colorScheme.primary;
      containerColor = colorScheme.primary.withOpacity(0.1);
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: iconColor.withOpacity(0.3), width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: containerColor,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: iconColor, size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              message,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: isError
                    ? colorScheme.onErrorContainer
                    : icon == Icons.check_circle_outline
                    ? Colors.green.shade800
                    : colorScheme.onPrimaryContainer,
                fontWeight: FontWeight.w500,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
