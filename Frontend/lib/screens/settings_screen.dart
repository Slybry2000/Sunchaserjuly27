import 'package:flutter/material.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> with TickerProviderStateMixin {
  bool notificationsEnabled = true;
  bool locationServicesEnabled = true;
  String temperatureUnit = 'Fahrenheit';
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Icon(
              Icons.settings,
              color: theme.colorScheme.onPrimaryContainer,
              size: 24,
            ),
            const SizedBox(width: 8),
            Text(
              'Settings',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.onPrimaryContainer,
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
      body: FadeTransition(
        opacity: _fadeAnimation,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // App Preferences Section
              _SectionHeader(
                icon: Icons.tune,
                title: 'App Preferences',
              ),
              const SizedBox(height: 16),
              
              _SettingsTile(
                leading: Icon(
                  Icons.notifications_outlined,
                  color: theme.colorScheme.primary,
                ),
                title: 'Notifications',
                subtitle: 'Get alerts about sunny weather',
                trailing: Switch(
                  value: notificationsEnabled,
                  onChanged: (value) {
                    setState(() {
                      notificationsEnabled = value;
                    });
                  },
                ),
              ),
              
              _SettingsTile(
                leading: Icon(
                  Icons.location_on_outlined,
                  color: theme.colorScheme.primary,
                ),
                title: 'Location Services',
                subtitle: 'Allow location access for better results',
                trailing: Switch(
                  value: locationServicesEnabled,
                  onChanged: (value) {
                    setState(() {
                      locationServicesEnabled = value;
                    });
                  },
                ),
              ),
              
              _SettingsTile(
                leading: Icon(
                  Icons.thermostat_outlined,
                  color: theme.colorScheme.primary,
                ),
                title: 'Temperature Unit',
                subtitle: temperatureUnit,
                trailing: Icon(
                  Icons.chevron_right,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
                onTap: () => _showTemperatureUnitDialog(),
              ),
              
              const SizedBox(height: 32),
              
              // About Section
              _SectionHeader(
                icon: Icons.info_outline,
                title: 'About',
              ),
              const SizedBox(height: 16),
              
              _SettingsTile(
                leading: Icon(
                  Icons.star_outline,
                  color: theme.colorScheme.secondary,
                ),
                title: 'Rate the App',
                subtitle: 'Help us improve',
                trailing: Icon(
                  Icons.chevron_right,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
                onTap: () => _showComingSoonSnackBar('Rate the App'),
              ),
              
              _SettingsTile(
                leading: Icon(
                  Icons.help_outline,
                  color: theme.colorScheme.secondary,
                ),
                title: 'Help & Support',
                subtitle: 'Get help using the app',
                trailing: Icon(
                  Icons.chevron_right,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
                onTap: () => _showComingSoonSnackBar('Help & Support'),
              ),
              
              _SettingsTile(
                leading: Icon(
                  Icons.privacy_tip_outlined,
                  color: theme.colorScheme.secondary,
                ),
                title: 'Privacy Policy',
                subtitle: 'How we protect your data',
                trailing: Icon(
                  Icons.chevron_right,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
                onTap: () => _showComingSoonSnackBar('Privacy Policy'),
              ),
              
              const SizedBox(height: 32),
              
              // App Version
              Center(
                child: Column(
                  children: [
                    Icon(
                      Icons.wb_sunny,
                      color: theme.colorScheme.primary,
                      size: 32,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Sunshine Spotter',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Version 1.0.0',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  void _showTemperatureUnitDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Temperature Unit'),
          // Minimal local RadioGroup implementation to follow the newer
          // API pattern (ancestor manages selection) while remaining
          // compatible across SDK versions. Uses GroupRadioListTile
          // which delegates selection to the enclosing RadioGroup.
          content: RadioGroup<String>(
            value: temperatureUnit,
            onChanged: (String? newValue) {
              if (newValue == null) return;
              setState(() {
                temperatureUnit = newValue;
              });
              Navigator.pop(context);
            },
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                GroupRadioListTile<String>(
                  title: const Text('Fahrenheit (°F)'),
                  value: 'Fahrenheit',
                ),
                GroupRadioListTile<String>(
                  title: const Text('Celsius (°C)'),
                  value: 'Celsius',
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showComingSoonSnackBar(String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$feature coming soon!'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String title;

  const _SectionHeader({
    required this.icon,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Row(
      children: [
        Icon(
          icon,
          color: theme.colorScheme.primary,
          size: 20,
        ),
        const SizedBox(width: 8),
        Text(
          title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.primary,
          ),
        ),
      ],
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final Widget leading;
  final String title;
  final String subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingsTile({
    required this.leading,
    required this.title,
    required this.subtitle,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Card(
      elevation: 2,
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        onTap: onTap,
        leading: leading,
        title: Text(
          title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        subtitle: Text(
          subtitle,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
          ),
        ),
        trailing: trailing,
        contentPadding: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );
  }
}

// Lightweight RadioGroup implementation to emulate the newer ancestor-driven
// radio API. This local helper avoids requiring a minimum Flutter SDK and
// keeps the settings screen backward-compatible.
class RadioGroup<T> extends InheritedWidget {
  final T value;
  final ValueChanged<T?> onChanged;

  const RadioGroup({
    required this.value,
    required this.onChanged,
    required super.child,
    super.key,
  }) : super();

  static RadioGroup<T>? of<T>(BuildContext context) {
    return context.dependOnInheritedWidgetOfExactType<RadioGroup<T>>();
  }

  @override
  bool updateShouldNotify(covariant RadioGroup<T> oldWidget) {
    return oldWidget.value != value;
  }
}

class GroupRadioListTile<T> extends StatelessWidget {
  final T value;
  final Widget title;

  const GroupRadioListTile({
    required this.value,
    required this.title,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final group = RadioGroup.of<T>(context);
    final theme = Theme.of(context);
    final selected = group != null && group.value == value;

    return ListTile(
      onTap: () => group?.onChanged(value),
      leading: Radio<T>(
        groupValue: group?.value,
        value: value,
        onChanged: group?.onChanged,
      ),
      title: DefaultTextStyle.merge(
        style: theme.textTheme.bodyMedium ?? const TextStyle(),
        child: title,
      ),
      selected: selected,
    );
  }
}