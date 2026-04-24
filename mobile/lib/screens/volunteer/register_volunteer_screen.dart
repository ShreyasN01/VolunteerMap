import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/volunteer_provider.dart';

class RegisterVolunteerScreen extends StatefulWidget {
  const RegisterVolunteerScreen({super.key});

  @override
  State<RegisterVolunteerScreen> createState() => _RegisterVolunteerScreenState();
}

class _RegisterVolunteerScreenState extends State<RegisterVolunteerScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  String _district = 'Pune';
  bool _available = true;

  final List<String> _allSkills = ['Medical', 'Teaching', 'Logistics', 'Cooking', 'Counselling', 'Construction', 'IT Support'];
  final List<String> _selectedSkills = [];

  final List<String> _allLanguages = ['Marathi', 'Hindi', 'English', 'Kannada', 'Telugu'];
  final List<String> _selectedLanguages = [];

  final List<String> _districts = [
    'Ahmednagar', 'Akola', 'Amravati', 'Aurangabad', 'Beed', 'Bhandara', 'Buldhana', 
    'Chandrapur', 'Dhule', 'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 
    'Kolhapur', 'Latur', 'Mumbai City', 'Mumbai Suburban', 'Nagpur', 'Nanded', 
    'Nandurbar', 'Nashik', 'Osmanabad', 'Palghar', 'Parbhani', 'Pune', 'Raigad', 
    'Ratnagiri', 'Sangli', 'Satara', 'Sindhururg', 'Solapur', 'Thane', 'Wardha', 
    'Washim', 'Yavatmal'
  ];

  void _submit() async {
    if (_formKey.currentState!.validate()) {
      final data = {
        'name': _nameController.text,
        'phone': _phoneController.text,
        'district': _district,
        'skills': _selectedSkills,
        'languages': _selectedLanguages,
        'available': _available,
        'location': {'latitude': 19.0760, 'longitude': 72.8777},
      };

      final success = await context.read<VolunteerProvider>().registerVolunteer(data);
      if (mounted) {
        if (success) {
          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              title: const Text('Success'),
              content: const Text('Volunteer registered successfully!'),
              actions: [
                TextButton(onPressed: () { Navigator.pop(context); Navigator.pop(context); }, child: const Text('OK')),
              ],
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Registration failed.')));
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Register Volunteer')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(labelText: 'Full Name', border: OutlineInputBorder()),
                validator: (v) => v!.isEmpty ? 'Please enter name' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _phoneController,
                decoration: const InputDecoration(labelText: 'Phone Number', border: OutlineInputBorder()),
                keyboardType: TextInputType.phone,
                validator: (v) => v!.isEmpty ? 'Please enter phone' : null,
              ),
              const SizedBox(height: 24),
              const Text('Skills', style: TextStyle(fontWeight: FontWeight.bold)),
              Wrap(
                spacing: 8,
                children: _allSkills.map((skill) {
                  final isSelected = _selectedSkills.contains(skill);
                  return FilterChip(
                    label: Text(skill),
                    selected: isSelected,
                    onSelected: (val) {
                      setState(() {
                        val ? _selectedSkills.add(skill) : _selectedSkills.remove(skill);
                      });
                    },
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),
              const Text('Languages', style: TextStyle(fontWeight: FontWeight.bold)),
              Wrap(
                spacing: 8,
                children: _allLanguages.map((lang) {
                  final isSelected = _selectedLanguages.contains(lang);
                  return FilterChip(
                    label: Text(lang),
                    selected: isSelected,
                    onSelected: (val) {
                      setState(() {
                        val ? _selectedLanguages.add(lang) : _selectedLanguages.remove(lang);
                      });
                    },
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),
              DropdownButtonFormField<String>(
                value: _district,
                items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                onChanged: (v) => setState(() => _district = v!),
                decoration: const InputDecoration(labelText: 'District', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              SwitchListTile(
                title: const Text('Available now'),
                value: _available,
                onChanged: (v) => setState(() => _available = v),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: _submit,
                style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50), backgroundColor: Colors.teal, foregroundColor: Colors.white),
                child: const Text('Register'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
