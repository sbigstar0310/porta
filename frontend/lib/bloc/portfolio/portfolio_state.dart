import 'package:equatable/equatable.dart';
import '../../models/portfolio.dart';

abstract class PortfolioState extends Equatable {
  const PortfolioState();

  @override
  List<Object?> get props => [];
}

class PortfolioInitial extends PortfolioState {}

class PortfolioLoading extends PortfolioState {}

class PortfolioLoadedState extends PortfolioState {
  final List<Portfolio> portfolios;
  final Portfolio? selectedPortfolio;

  const PortfolioLoadedState({
    required this.portfolios,
    this.selectedPortfolio,
  });

  double get totalPortfolioValue {
    if (portfolios.isEmpty) return 0.0;
    return portfolios.first.totalValue ?? 0.0;
  }

  double get totalProfitLoss {
    if (portfolios.isEmpty) return 0.0;
    return portfolios.first.totalUnrealizedPnl ?? 0.0;
  }

  double get totalProfitLossPercentage {
    if (portfolios.isEmpty) return 0.0;
    return portfolios.first.totalUnrealizedPnlPct ?? 0.0;
  }

  @override
  List<Object?> get props => [portfolios, selectedPortfolio];

  PortfolioLoadedState copyWith({
    List<Portfolio>? portfolios,
    Portfolio? selectedPortfolio,
  }) {
    return PortfolioLoadedState(
      portfolios: portfolios ?? this.portfolios,
      selectedPortfolio: selectedPortfolio ?? this.selectedPortfolio,
    );
  }
}

class PortfolioError extends PortfolioState {
  final String message;

  /// 이메일 미인증(403 EMAIL_NOT_VERIFIED)으로 인한 실패면 true.
  /// 화면에서 일반 에러 대신 이메일 인증 안내를 표시한다.
  final bool requiresEmailVerification;

  const PortfolioError(this.message, {this.requiresEmailVerification = false});

  @override
  List<Object> get props => [message, requiresEmailVerification];
}
