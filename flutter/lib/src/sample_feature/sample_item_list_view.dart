import 'package:flutter/material.dart';

import '../settings/settings_view.dart';
import 'sample_item.dart';
import 'sample_item_details_view.dart';
import 'package:dio/dio.dart';
import '../globals.dart';
import 'dart:convert';

class SampleItemListView extends StatefulWidget {
  const SampleItemListView({Key? key}) : super(key: key);
  static const routeName = '/';
  @override
  State<StatefulWidget> createState() => SampleItemListViewState();
}

/// Displays a list of SampleItems.
class SampleItemListViewState extends State<SampleItemListView> {
  List<SampleItem> items = [];

  @override
  void initState() {
    super.initState();
    initAsync();

  }
  void initAsync() async {

    var response;
    try {
      response = await Dio().get(PREFIX + "/birds");
    } catch (e) {
      print(e);
      return;
    }
    var birds = jsonDecode(response.data);
    int i = 0;
    birds.forEach((k, v)  {
    print('$i $k $v');
    items.add(SampleItem(i, k, v));
    i += 1;
    });
    setState(() {
    });
  }





  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BirdNet App (Last 24 Hours)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              // Navigate to the settings page. If the user leaves and returns
              // to the app after it has been killed while running in the
              // background, the navigation stack is restored.
              Navigator.restorablePushNamed(context, SettingsView.routeName);
            },
          ),
        ],
      ),

      // To work with lists that may contain a large number of items, it’s best
      // to use the ListView.builder constructor.
      //
      // In contrast to the default ListView constructor, which requires
      // building all Widgets up front, the ListView.builder constructor lazily
      // builds Widgets as they’re scrolled into view.
      body: ListView.builder(
        // Providing a restorationId allows the ListView to restore the
        // scroll position when a user leaves and returns to the app after it
        // has been killed while running in the background.
        restorationId: 'sampleItemListView',
        itemCount: items.length,
        itemBuilder: (BuildContext context, int index) {
          final item = items[index];

          return ListTile(
            title: Text('${item.name}. Detected: ${item.count}'),
            leading: const CircleAvatar(
              // Display the Flutter Logo image asset.
              foregroundImage: AssetImage('assets/images/flutter_logo.png'),
            ),
            onTap: () {
              // Navigate to the details page. If the user leaves and returns to
              // the app after it has been killed while running in the
              // background, the navigation stack is restored.
              Navigator.restorablePushNamed(
                context,
                SampleItemDetailsView.routeName,
                arguments: item.name,
              );
            }
          );
        },
      ),
    );
  }
}
