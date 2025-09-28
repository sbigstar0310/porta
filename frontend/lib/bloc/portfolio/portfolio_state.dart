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

  const PortfolioError(this.message);

  @override
  List<Object> get props => [message];
}
