import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import '../../providers/survey_provider.dart';
import '../../models/survey.dart';
import '../../widgets/survey_card.dart';

class NeedsMapScreen extends StatefulWidget {
  const NeedsMapScreen({super.key});

  @override
  State<NeedsMapScreen> createState() => _NeedsMapScreenState();
}

class _NeedsMapScreenState extends State<NeedsMapScreen> {
  String _selectedCategory = 'All';
  final List<String> _categories = ['All', 'Healthcare', 'Food', 'Education', 'Sanitation', 'Employment'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SurveyProvider>().fetchSurveys();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          Consumer<SurveyProvider>(
            builder: (context, provider, child) {
              final surveys = provider.filterByCategory(_selectedCategory);
              
              return FlutterMap(
                options: const MapOptions(
                  initialCenter: LatLng(19.7515, 75.7139), // Maharashtra
                  initialZoom: 7.0,
                ),
                children: [
                  TileLayer(
                    urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'com.volunteermap.app',
                  ),
                  CircleLayer(
                    circles: surveys.map((s) {
                      return CircleMarker(
                        point: LatLng(s.latitude, s.longitude),
                        color: s.categoryColor.withValues(alpha: 0.6),
                        borderStrokeWidth: 2,
                        useRadiusInMeter: false,
                        radius: s.urgencyScore / 5, // scaled for visibility
                      );
                    }).toList(),
                  ),
                  MarkerLayer(
                    markers: surveys.map((s) {
                      return Marker(
                        point: LatLng(s.latitude, s.longitude),
                        width: 40,
                        height: 40,
                        child: GestureDetector(
                          onTap: () => _showSurveyDetails(context, s),
                          child: Icon(Icons.location_on, color: s.categoryColor, size: 30),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              );
            },
          ),
          
          // Filter Chips at top
          Positioned(
            top: 50,
            left: 0,
            right: 0,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: _categories.map((cat) {
                  final isSelected = _selectedCategory == cat;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: FilterChip(
                      label: Text(cat),
                      selected: isSelected,
                      onSelected: (val) => setState(() => _selectedCategory = cat),
                      backgroundColor: Colors.white,
                      selectedColor: Colors.teal[100],
                      labelStyle: TextStyle(color: isSelected ? Colors.teal[900] : Colors.black, fontWeight: isSelected ? FontWeight.bold : FontWeight.normal),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        child: const Icon(Icons.my_location),
      ),
    );
  }

  void _showSurveyDetails(BuildContext context, Survey survey) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Padding(
        padding: const EdgeInsets.all(16.0),
        child: SurveyCard(survey: survey),
      ),
    );
  }
}
