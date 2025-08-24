import 'package:flutter/material.dart';
import 'package:sunshine_spotter/models/location.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:sunshine_spotter/screens/detail_screen.dart';
import 'package:sunshine_spotter/services/data_service.dart';
import 'package:sunshine_spotter/widgets/sunshine_spot_card.dart';

class ResultsScreen extends StatefulWidget {
  final LocationData? location;
  final double radius;
  final String? q;

  const ResultsScreen({
    super.key,
    this.location,
    required this.radius,
    this.q,
  });

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> with TickerProviderStateMixin {
  List<SunshineSpot> spots = [];
  bool isLoading = true;
  String? errorMessage;
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _searchSpots();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _searchSpots() async {
    try {
      final results = await DataService.searchSpots(
        latitude: widget.location?.latitude ?? 0.0,
        longitude: widget.location?.longitude ?? 0.0,
        radiusMiles: widget.radius,
        q: widget.q,
      );
      
      if (mounted) {
        setState(() {
          spots = results;
          isLoading = false;
        });
        _animationController.forward();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          errorMessage = 'Failed to find sunny spots. Please try again.';
          isLoading = false;
        });
      }
    }
  }

  Future<void> _toggleFavorite(SunshineSpot spot) async {
    if (spot.isFavorite) {
      await DataService.removeFromFavorites(spot.id);
    } else {
      await DataService.addToFavorites(spot);
    }
    
    // Update the spot in the list
    setState(() {
      final index = spots.indexWhere((s) => s.id == spot.id);
      if (index != -1) {
        spots[index] = spot.copyWith(isFavorite: !spot.isFavorite);
      }
    });
  }

  String get _radiusText {
    if (widget.radius == 25) return 'Nearby';
    if (widget.radius == 100) return 'Day Trip';
    if (widget.radius == 200) return 'Road Trip';
    return '${widget.radius.toInt()} miles';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Sunny Spots',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.onPrimaryContainer,
              ),
            ),
            Text(
              '${widget.q != null ? '"${widget.q}"' : _radiusText} • ${spots.length} found',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.8),
              ),
            ),
          ],
        ),
        leading: IconButton(
          icon: Icon(
            Icons.arrow_back,
            color: theme.colorScheme.onPrimaryContainer,
          ),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Finding sunny spots...'),
          ],
        ),
      );
    }

    if (errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              errorMessage!,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  isLoading = true;
                  errorMessage = null;
                });
                _searchSpots();
              },
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (spots.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.wb_sunny_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 16),
            const Text(
              'No sunny spots found',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            Text(
              'Try expanding your search area',
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
          ],
        ),
      );
    }

    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return Transform.translate(
          offset: Offset(0, 50 * (1 - _animationController.value)),
          child: Opacity(
            opacity: _animationController.value,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: spots.length,
              itemBuilder: (context, index) {
                final spot = spots[index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: SunshineSpotCard(
                    spot: spot,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => DetailScreen(spot: spot),
                      ),
                    ),
                    onFavoriteToggle: () => _toggleFavorite(spot),
                  ),
                );
              },
            ),
          ),
        );
      },
    );
  }
}