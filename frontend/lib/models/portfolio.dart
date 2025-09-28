class Portfolio {
  final int id;
  final int userId;
  final String baseCurrency;
  final double cash;
  final DateTime updatedAt;
  final List<Position> positions;
  final double? totalStockValue;
  final double? totalValue;
  final double? totalUnrealizedPnl;
  final double? totalUnrealizedPnlPct;

  Portfolio({
    required this.id,
    required this.userId,
    required this.baseCurrency,
    required this.cash,
    required this.updatedAt,
    required this.positions,
    this.totalStockValue,
    this.totalValue,
    this.totalUnrealizedPnl,
    this.totalUnrealizedPnlPct,
  });

  factory Portfolio.fromJson(Map<String, dynamic> json) {
    return Portfolio(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      baseCurrency: json['base_currency'] as String,
      cash: double.parse(json['cash'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      positions: (json['positions'] as List? ?? [])
          .map((position) => Position.fromJson(position))
          .toList(),
      totalStockValue: json['total_stock_value'] != null
          ? double.parse(json['total_stock_value'] as String)
          : null,
      totalValue: json['total_value'] != null
          ? double.parse(json['total_value'] as String)
          : null,
      totalUnrealizedPnl: json['total_unrealized_pnl'] != null
          ? double.parse(json['total_unrealized_pnl'] as String)
          : null,
      totalUnrealizedPnlPct: json['total_unrealized_pnl_pct'] != null
          ? double.parse(json['total_unrealized_pnl_pct'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'base_currency': baseCurrency,
      'cash': cash,
      'updated_at': updatedAt.toIso8601String(),
      'positions': positions.map((p) => p.toJson()).toList(),
      'total_stock_value': totalStockValue,
      'total_value': totalValue,
      'total_unrealized_pnl': totalUnrealizedPnl,
      'total_unrealized_pnl_pct': totalUnrealizedPnlPct,
    };
  }

  Portfolio copyWith({
    int? id,
    int? userId,
    String? baseCurrency,
    double? cash,
    DateTime? updatedAt,
    List<Position>? positions,
    double? totalStockValue,
    double? totalValue,
    double? totalUnrealizedPnl,
    double? totalUnrealizedPnlPct,
  }) {
    return Portfolio(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      baseCurrency: baseCurrency ?? this.baseCurrency,
      cash: cash ?? this.cash,
      updatedAt: updatedAt ?? this.updatedAt,
      positions: positions ?? this.positions,
      totalStockValue: totalStockValue ?? this.totalStockValue,
      totalValue: totalValue ?? this.totalValue,
      totalUnrealizedPnl: totalUnrealizedPnl ?? this.totalUnrealizedPnl,
      totalUnrealizedPnlPct:
          totalUnrealizedPnlPct ?? this.totalUnrealizedPnlPct,
    );
  }

  // Computed properties for UI compatibility
  String get name => 'Portfolio'; // Default name since backend doesn't have it
  List<PortfolioItem> get items =>
      positions.map((p) => PortfolioItem.fromPosition(p)).toList();
}

class PortfolioItem {
  final String symbol;
  final String name;
  final double quantity;
  final double averagePrice;
  final double currentPrice;
  final double totalValue;

  PortfolioItem({
    required this.symbol,
    required this.name,
    required this.quantity,
    required this.averagePrice,
    required this.currentPrice,
    required this.totalValue,
  });

  factory PortfolioItem.fromPosition(Position position) {
    return PortfolioItem(
      symbol: position.ticker,
      name: position.ticker, // Backend doesn't have company name
      quantity: position.totalShares,
      averagePrice: position.avgBuyPrice,
      currentPrice: position.currentPrice ?? position.avgBuyPrice,
      totalValue:
          position.currentMarketValue ??
          (position.totalShares * position.avgBuyPrice),
    );
  }

  factory PortfolioItem.fromJson(Map<String, dynamic> json) {
    return PortfolioItem(
      symbol: json['symbol'] as String,
      name: json['name'] as String,
      quantity: (json['quantity'] as num).toDouble(),
      averagePrice: double.parse(json['average_price'] as String),
      currentPrice: double.parse(json['current_price'] as String),
      totalValue: double.parse(json['total_value'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'symbol': symbol,
      'name': name,
      'quantity': quantity,
      'average_price': averagePrice,
      'current_price': currentPrice,
      'total_value': totalValue,
    };
  }

  double get profitLoss => totalValue - (averagePrice * quantity);
  double get profitLossPercentage =>
      (profitLoss / (averagePrice * quantity)) * 100;
}

class Position {
  final int id;
  final int portfolioId;
  final String ticker;
  final double totalShares;
  final double avgBuyPrice;
  final DateTime updatedAt;
  final double? currentPrice;
  final double? currentMarketValue;
  final double? unrealizedPnl;
  final double? unrealizedPnlPct;

  Position({
    required this.id,
    required this.portfolioId,
    required this.ticker,
    required this.totalShares,
    required this.avgBuyPrice,
    required this.updatedAt,
    this.currentPrice,
    this.currentMarketValue,
    this.unrealizedPnl,
    this.unrealizedPnlPct,
  });

  factory Position.fromJson(Map<String, dynamic> json) {
    return Position(
      id: json['id'] as int,
      portfolioId: json['portfolio_id'] as int,
      ticker: json['ticker'] as String,
      totalShares: (json['total_shares'] as num).toDouble(),
      avgBuyPrice: (json['avg_buy_price'] as num).toDouble(),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      currentPrice: json['current_price'] != null
          ? (json['current_price'] as num).toDouble()
          : null,
      currentMarketValue: json['current_market_value'] != null
          ? (json['current_market_value'] as num).toDouble()
          : null,
      unrealizedPnl: json['unrealized_pnl'] != null
          ? (json['unrealized_pnl'] as num).toDouble()
          : null,
      unrealizedPnlPct: json['unrealized_pnl_pct'] != null
          ? (json['unrealized_pnl_pct'] as num).toDouble()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'portfolio_id': portfolioId,
      'ticker': ticker,
      'total_shares': totalShares,
      'avg_buy_price': avgBuyPrice,
      'updated_at': updatedAt.toIso8601String(),
      'current_price': currentPrice,
      'current_market_value': currentMarketValue,
      'unrealized_pnl': unrealizedPnl,
      'unrealized_pnl_pct': unrealizedPnlPct,
    };
  }
}
