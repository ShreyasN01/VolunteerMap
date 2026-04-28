import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

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
    final user = context.watch<AuthProvider>().user;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'VolunteerMap',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            if (user != null)
              Text(
                'Welcome, ${user['name']}',
                style: TextStyle(fontSize: 10, color: Colors.teal[800], fontWeight: FontWeight.bold),
              ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: Colors.redAccent),
            onPressed: () {
              context.read<AuthProvider>().logout();
              Navigator.pushReplacementNamed(context, '/login');
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
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
