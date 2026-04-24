import 'package:flutter/material.dart';
import 'package:flutter_speed_dial/flutter_speed_dial.dart';
import 'dashboard/dashboard_screen.dart';
import 'map/needs_map_screen.dart';
import 'survey/survey_list_screen.dart';
import 'volunteer/volunteer_list_screen.dart';
import 'survey/submit_survey_screen.dart';
import 'volunteer/register_volunteer_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const DashboardScreen(),
    const NeedsMapScreen(),
    const SurveyListScreen(),
    const VolunteerListScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: Colors.teal[700],
        unselectedItemColor: Colors.grey,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.map), label: 'Map'),
          BottomNavigationBarItem(icon: Icon(Icons.list_alt), label: 'Surveys'),
          BottomNavigationBarItem(icon: Icon(Icons.people), label: 'Volunteers'),
        ],
      ),
      floatingActionButton: SpeedDial(
        icon: Icons.add,
        activeIcon: Icons.close,
        backgroundColor: const Color(0xFF00897B),
        foregroundColor: Colors.white,
        children: [
          SpeedDialChild(
            child: const Icon(Icons.assignment),
            label: 'Submit Survey',
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SubmitSurveyScreen())),
          ),
          SpeedDialChild(
            child: const Icon(Icons.person_add),
            label: 'Register Volunteer',
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RegisterVolunteerScreen())),
          ),
        ],
      ),
    );
  }
}
