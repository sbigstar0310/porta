import 'package:flutter/material.dart';

class CustomButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final ButtonStyle? style;
  final Widget? icon;
  final bool expanded;

  const CustomButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.style,
    this.icon,
    this.expanded = false,
  });

  @override
  Widget build(BuildContext context) {
    Widget button;

    if (icon != null) {
      button = ElevatedButton.icon(
        onPressed: isLoading ? null : onPressed,
        style: style,
        icon: isLoading
            ? const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : icon!,
        label: Text(text),
      );
    } else {
      button = ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: style,
        child: isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Text(text),
      );
    }

    return expanded ? SizedBox(width: double.infinity, child: button) : button;
  }
}

class CustomOutlinedButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final ButtonStyle? style;
  final Widget? icon;
  final bool expanded;

  const CustomOutlinedButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.style,
    this.icon,
    this.expanded = false,
  });

  @override
  Widget build(BuildContext context) {
    Widget button;

    if (icon != null) {
      button = OutlinedButton.icon(
        onPressed: isLoading ? null : onPressed,
        style: style,
        icon: isLoading
            ? const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : icon!,
        label: Text(text),
      );
    } else {
      button = OutlinedButton(
        onPressed: isLoading ? null : onPressed,
        style: style,
        child: isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Text(text),
      );
    }

    return expanded ? SizedBox(width: double.infinity, child: button) : button;
  }
}

class CustomTextButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final ButtonStyle? style;
  final Widget? icon;

  const CustomTextButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.style,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    if (icon != null) {
      return TextButton.icon(
        onPressed: isLoading ? null : onPressed,
        style: style,
        icon: isLoading
            ? const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : icon!,
        label: Text(text),
      );
    } else {
      return TextButton(
        onPressed: isLoading ? null : onPressed,
        style: style,
        child: isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Text(text),
      );
    }
  }
}
