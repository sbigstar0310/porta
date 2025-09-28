import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../bloc/portfolio/portfolio_bloc.dart';
import '../../bloc/portfolio/portfolio_event.dart';
import '../../bloc/portfolio/portfolio_state.dart';
import '../../models/portfolio.dart';
import '../../utils/currency_formatter.dart';

class PortfolioScreen extends StatefulWidget {
  const PortfolioScreen({super.key});

  @override
  State<PortfolioScreen> createState() => _PortfolioScreenState();
}

class _PortfolioScreenState extends State<PortfolioScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<PortfolioBloc>().add(PortfolioLoadRequested());
    });
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<PortfolioBloc, PortfolioState>(
      builder: (context, state) {
        if (state is PortfolioLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        if (state is PortfolioError) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  state.message,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => context.read<PortfolioBloc>().add(
                    PortfolioLoadRequested(),
                  ),
                  child: const Text('다시 시도'),
                ),
              ],
            ),
          );
        }

        if (state is PortfolioLoadedState) {
          if (state.portfolios.isEmpty) {
            return const _EmptyPortfolioWidget();
          }

          final portfolio =
              state.portfolios.first; // Use first portfolio as main portfolio

          return Scaffold(
            floatingActionButton: FloatingActionButton(
              onPressed: () => context.go('/position/add'),
              tooltip: '포지션 추가',
              child: const Icon(Icons.add),
            ),
            body: RefreshIndicator(
              onRefresh: () async {
                context.read<PortfolioBloc>().add(PortfolioLoadRequested());
              },
              child: CustomScrollView(
                slivers: [
                  // Portfolio summary card
                  SliverToBoxAdapter(child: _buildSummaryCard(portfolio)),

                  // Portfolio positions header
                  SliverToBoxAdapter(child: _buildPositionsHeader(portfolio)),

                  // Portfolio positions list
                  if (portfolio.positions.isEmpty)
                    const SliverToBoxAdapter(child: _EmptyPositionsWidget())
                  else
                    SliverList(
                      delegate: SliverChildBuilderDelegate((context, index) {
                        final position = portfolio.positions[index];
                        return _buildPositionCard(position, portfolio);
                      }, childCount: portfolio.positions.length),
                    ),

                  // Add some bottom padding
                  const SliverToBoxAdapter(child: SizedBox(height: 100)),
                ],
              ),
            ),
          );
        }

        return const SizedBox.shrink();
      },
    );
  }

  Widget _buildSummaryCard(Portfolio portfolio) {
    final currencyFormat = CurrencyFormatter.createFormatter(
      portfolio.baseCurrency,
    );
    final percentFormat = NumberFormat('#,##0.00');

    return Container(
      margin: const EdgeInsets.all(24),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Theme.of(context).colorScheme.primary,
            Theme.of(context).colorScheme.primary.withOpacity(0.8),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '내 포트폴리오',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: Theme.of(context).colorScheme.onPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${portfolio.positions.length}개 종목',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(
                          context,
                        ).colorScheme.onPrimary.withOpacity(0.8),
                      ),
                    ),
                  ],
                ),
              ),
              IconButton.outlined(
                onPressed: () => context.go('/portfolio/edit'),
                icon: Icon(
                  Icons.edit_outlined,
                  color: Theme.of(context).colorScheme.onPrimary,
                ),
                style: IconButton.styleFrom(
                  side: BorderSide(
                    color: Theme.of(
                      context,
                    ).colorScheme.onPrimary.withOpacity(0.3),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Text(
            '총 자산 가치',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Theme.of(context).colorScheme.onPrimary.withOpacity(0.9),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            currencyFormat.format(portfolio.totalValue ?? 0),
            style: Theme.of(context).textTheme.headlineLarge?.copyWith(
              color: Theme.of(context).colorScheme.onPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: _buildSummaryItem(
                  '보유 현금',
                  currencyFormat.format(portfolio.cash),
                  Icons.account_balance_wallet_outlined,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildSummaryItem(
                  '주식 가치',
                  currencyFormat.format(portfolio.totalStockValue ?? 0),
                  Icons.trending_up_outlined,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildPnlItem(
                  '총 손익',
                  currencyFormat.format(portfolio.totalUnrealizedPnl ?? 0),
                  (portfolio.totalUnrealizedPnl ?? 0) >= 0,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildPnlItem(
                  '수익률',
                  '${percentFormat.format(portfolio.totalUnrealizedPnlPct ?? 0)}%',
                  (portfolio.totalUnrealizedPnlPct ?? 0) >= 0,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryItem(String title, String value, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.onPrimary.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                size: 16,
                color: Theme.of(context).colorScheme.onPrimary.withOpacity(0.8),
              ),
              const SizedBox(width: 8),
              Text(
                title,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(
                    context,
                  ).colorScheme.onPrimary.withOpacity(0.8),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Theme.of(context).colorScheme.onPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPnlItem(String title, String value, bool isPositive) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: (isPositive ? Colors.green : Colors.red).withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onPrimary.withOpacity(0.8),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: isPositive ? Colors.greenAccent : Colors.redAccent,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPositionsHeader(Portfolio portfolio) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24),
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Icon(
            Icons.business_outlined,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(width: 12),
          Text(
            '보유 종목 (${portfolio.positions.length})',
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildPositionCard(Position position, Portfolio portfolio) {
    final currencyFormat = CurrencyFormatter.createFormatter(
      portfolio.baseCurrency,
    );
    final percentFormat = NumberFormat('#,##0.00');
    final sharesFormat = NumberFormat('#,##0.###');

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      child: Card(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: InkWell(
          onTap: () => context.go('/position/edit/${position.id}'),
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Stock header
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.primaryContainer,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        Icons.trending_up,
                        color: Theme.of(context).colorScheme.onPrimaryContainer,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            position.ticker,
                            style: Theme.of(context).textTheme.titleLarge
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          Text(
                            '${sharesFormat.format(position.totalShares)}주',
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onSurface.withOpacity(0.6),
                                ),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          currencyFormat.format(
                            position.currentMarketValue ?? 0,
                          ),
                          style: Theme.of(context).textTheme.titleLarge
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        Text(
                          '${(position.unrealizedPnlPct ?? 0) >= 0 ? '+' : ''}${percentFormat.format(position.unrealizedPnlPct ?? 0)}%',
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(
                                color: (position.unrealizedPnlPct ?? 0) >= 0
                                    ? Colors.green
                                    : Colors.red,
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                // Position details
                Row(
                  children: [
                    Expanded(
                      child: _buildPositionDetail(
                        '평균 단가',
                        currencyFormat.format(position.avgBuyPrice),
                        Icons.payment_outlined,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _buildPositionDetail(
                        '현재 가격',
                        currencyFormat.format(
                          position.currentPrice ?? position.avgBuyPrice,
                        ),
                        Icons.price_change_outlined,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: _buildPositionDetail(
                        '평가 손익',
                        currencyFormat.format(position.unrealizedPnl ?? 0),
                        Icons.account_balance_outlined,
                        isProfit: (position.unrealizedPnl ?? 0) >= 0,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _buildPositionDetail(
                        '손익률',
                        '${percentFormat.format(position.unrealizedPnlPct ?? 0)}%',
                        Icons.trending_up_outlined,
                        isProfit: (position.unrealizedPnlPct ?? 0) >= 0,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPositionDetail(
    String title,
    String value,
    IconData icon, {
    bool? isProfit,
  }) {
    Color? textColor;
    if (isProfit != null) {
      textColor = isProfit ? Colors.green : Colors.red;
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                size: 16,
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              ),
              const SizedBox(width: 8),
              Text(
                title,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(
                    context,
                  ).colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: textColor,
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyPositionsWidget extends StatelessWidget {
  const _EmptyPositionsWidget();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.business_outlined,
            size: 64,
            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.4),
          ),
          const SizedBox(height: 16),
          Text(
            '보유 종목이 없습니다',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '종목을 추가하여 포트폴리오를 구성해보세요',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.4),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => context.go('/position/add'),
            icon: const Icon(Icons.add),
            label: const Text('종목 추가하기'),
          ),
        ],
      ),
    );
  }
}

class _EmptyPortfolioWidget extends StatelessWidget {
  const _EmptyPortfolioWidget();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.account_balance_wallet_outlined,
            size: 64,
            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.4),
          ),
          const SizedBox(height: 16),
          Text(
            '포트폴리오가 없습니다',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '첫 번째 포트폴리오를 만들어보세요',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.4),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => context.go('/portfolio/edit'),
            icon: const Icon(Icons.add),
            label: const Text('포트폴리오 만들기'),
          ),
        ],
      ),
    );
  }
}
