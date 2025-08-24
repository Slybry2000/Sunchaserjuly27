import 'package:flutter/material.dart';

class AreaSelectionCard extends StatelessWidget {
  final double selectedRadius;
  final Function(double) onAreaSelected;

  const AreaSelectionCard({
    super.key,
    required this.selectedRadius,
    required this.onAreaSelected,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    final List<Map<String, dynamic>> areaOptions = [
      {'name': 'Nearby', 'radius': 25.0, 'description': '25 miles', 'icon': Icons.near_me},
      {'name': 'Day Trip', 'radius': 100.0, 'description': '100 miles', 'icon': Icons.directions_car},
      {'name': 'Road Trip', 'radius': 200.0, 'description': '200 miles', 'icon': Icons.map},
    ];
    
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.explore,
                  color: theme.colorScheme.primary,
                  size: 24,
                ),
                const SizedBox(width: 8),
                Text(
                  'Search Area',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            Row(
              children: areaOptions.map((option) {
                final bool isSelected = selectedRadius == option['radius'];
                return Expanded(
                  child: Padding(
                    padding: EdgeInsets.only(
                      right: option == areaOptions.last ? 0 : 8,
                      left: option == areaOptions.first ? 0 : 8,
                    ),
                    child: GestureDetector(
                      onTap: () => onAreaSelected(option['radius']),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
                        decoration: BoxDecoration(
                          color: isSelected 
                            ? theme.colorScheme.primary
                            : theme.colorScheme.surface,
                          border: Border.all(
                            color: isSelected 
                              ? theme.colorScheme.primary
                              : theme.colorScheme.outline.withValues(alpha: 0.3),
                          ),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              option['icon'],
                              color: isSelected 
                                ? theme.colorScheme.onPrimary
                                : theme.colorScheme.primary,
                              size: 24,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              option['name'],
                              style: theme.textTheme.labelLarge?.copyWith(
                                color: isSelected 
                                  ? theme.colorScheme.onPrimary
                                  : theme.colorScheme.onSurface,
                                fontWeight: FontWeight.w600,
                              ),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              option['description'],
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: isSelected 
                                  ? theme.colorScheme.onPrimary.withValues(alpha: 0.8)
                                  : theme.colorScheme.onSurface.withValues(alpha: 0.6),
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}