class StockSearchResult {
  final String ticker;
  final String companyName;

  const StockSearchResult({required this.ticker, required this.companyName});

  factory StockSearchResult.fromJson(Map<String, dynamic> json) {
    return StockSearchResult(
      ticker: json['ticker'] as String,
      companyName: json['company_name'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {'ticker': ticker, 'company_name': companyName};
  }

  @override
  String toString() {
    return 'StockSearchResult(ticker: $ticker, companyName: $companyName)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is StockSearchResult &&
        other.ticker == ticker &&
        other.companyName == companyName;
  }

  @override
  int get hashCode {
    return ticker.hashCode ^ companyName.hashCode;
  }
}
