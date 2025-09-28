import 'package:flutter/material.dart';
import 'dart:async';
import '../../services/api_service.dart';
import '../../models/stock_search_result.dart';

class StockSearchField extends StatefulWidget {
  final TextEditingController controller;
  final String? Function(String?)? validator;
  final String hintText;
  final InputDecoration? decoration;

  const StockSearchField({
    super.key,
    required this.controller,
    this.validator,
    this.hintText = 'AAPL, MSFT 등',
    this.decoration,
  });

  @override
  State<StockSearchField> createState() => _StockSearchFieldState();
}

class _StockSearchFieldState extends State<StockSearchField> {
  final ApiService _apiService = ApiService();
  final FocusNode _focusNode = FocusNode();
  final LayerLink _layerLink = LayerLink();
  OverlayEntry? _overlayEntry;

  List<StockSearchResult> _searchResults = [];
  bool _isSearching = false;
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onTextChanged);
    _focusNode.addListener(_onFocusChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onTextChanged);
    _focusNode.removeListener(_onFocusChanged);
    _focusNode.dispose();
    _debounceTimer?.cancel();
    _removeOverlay();
    super.dispose();
  }

  void _onTextChanged() {
    final query = widget.controller.text.trim();

    // 디바운스: 500ms 후에 검색 실행
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 500), () {
      if (mounted) {
        if (query.isNotEmpty && query.length >= 1) {
          _searchStock(query);
        } else {
          _clearResults();
        }
      }
    });
  }

  void _onFocusChanged() {
    if (!_focusNode.hasFocus) {
      // 포커스를 잃으면 잠깐 후에 오버레이 제거 (클릭 이벤트 처리를 위한 딜레이)
      Timer(const Duration(milliseconds: 200), () {
        if (mounted) {
          _removeOverlay();
        }
      });
    }
  }

  Future<void> _searchStock(String query) async {
    if (!mounted) return;

    setState(() {
      _isSearching = true;
    });

    try {
      final results = await _apiService.searchStock(query);
      if (mounted) {
        setState(() {
          _searchResults = results;
          _isSearching = false;
        });
        _showOverlay();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _searchResults = [];
          _isSearching = false;
        });
        debugPrint('종목 검색 오류: $e');
      }
    }
  }

  void _clearResults() {
    if (mounted) {
      setState(() {
        _searchResults = [];
        _isSearching = false;
      });
      _removeOverlay();
    }
  }

  void _onResultTap(StockSearchResult result) {
    widget.controller.text = result.ticker;
    _clearResults();
    _focusNode.unfocus();
  }

  void _showOverlay() {
    if (!mounted || _overlayEntry != null || _searchResults.isEmpty) return;

    _overlayEntry = OverlayEntry(
      builder: (context) => Stack(
        children: [
          // 투명한 배경 - 탭하면 오버레이 닫기
          Positioned.fill(
            child: GestureDetector(
              onTap: () {
                if (mounted) {
                  _removeOverlay();
                }
              },
              child: Container(color: Colors.transparent),
            ),
          ),
          // 실제 드롭다운 리스트
          Positioned(
            width: MediaQuery.of(context).size.width - 48, // 좌우 패딩 고려
            child: CompositedTransformFollower(
              link: _layerLink,
              showWhenUnlinked: false,
              offset: const Offset(0, 60), // TextFormField 아래에 위치
              child: Material(
                elevation: 4,
                borderRadius: BorderRadius.circular(8),
                child: Container(
                  constraints: const BoxConstraints(maxHeight: 200),
                  decoration: BoxDecoration(
                    color: Theme.of(context).cardColor,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: Theme.of(context).dividerColor,
                      width: 1,
                    ),
                  ),
                  child: ListView.builder(
                    padding: EdgeInsets.zero,
                    shrinkWrap: true,
                    itemCount: _searchResults.length,
                    itemBuilder: (context, index) {
                      final result = _searchResults[index];
                      return ListTile(
                        dense: true,
                        title: Row(
                          children: [
                            Text(
                              result.ticker,
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 16,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                result.companyName,
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Theme.of(
                                    context,
                                  ).textTheme.bodySmall?.color,
                                  fontWeight: FontWeight.w400,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                        trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                        onTap: () {
                          if (mounted) {
                            _onResultTap(result);
                          }
                        },
                      );
                    },
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );

    try {
      Overlay.of(context).insert(_overlayEntry!);
    } catch (e) {
      debugPrint('Overlay 삽입 오류: $e');
      _overlayEntry = null;
    }
  }

  void _removeOverlay() {
    try {
      _overlayEntry?.remove();
    } catch (e) {
      debugPrint('Overlay 제거 오류: $e');
    } finally {
      _overlayEntry = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return CompositedTransformTarget(
      link: _layerLink,
      child: TextFormField(
        controller: widget.controller,
        focusNode: _focusNode,
        decoration:
            widget.decoration ??
            InputDecoration(
              hintText: widget.hintText,
              border: const OutlineInputBorder(),
              suffixIcon: _isSearching
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: Padding(
                        padding: EdgeInsets.all(12),
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    )
                  : const Icon(Icons.search),
            ),
        textCapitalization: TextCapitalization.characters,
        validator: widget.validator,
      ),
    );
  }
}
