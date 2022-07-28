import 'package:flutter/material.dart';
import 'dart:convert';
import '../settings/settings_view.dart';
import 'sample_item.dart';
import 'sample_item_details_view.dart';
import 'package:dio/dio.dart';
import '../globals.dart';

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

class _BarChart extends StatefulWidget {
  const _BarChart({Key? key}) : super(key: key);
  @override
  State<StatefulWidget> createState() => BarChartState();
}

class BarChartState extends State<_BarChart>{

  List<BarChartGroupData> barGroups = [];
  List<String> labels = [];
  List<int> counts = [];
  List<DataRow> rows = [];
  final double maxY = 20;
  bool is_loaded = false;
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
    barGroups = [];
    birds.forEach((k, v)  {
    print('$i $k $v');

    var row = DataRow(
          cells: <DataCell>[
            DataCell(Text(k)),
            DataCell(Text(v.toString())),
          ],
        );
    rows.add(row);




    labels.add(k);
    counts.add(v);
    var val = BarChartGroupData(
      x: i,
      barRods: [
        BarChartRodData(
          toY: v < maxY ? v : maxY - 1,
          gradient: _barsGradient,
        )
      ],
      showingTooltipIndicators: [0],
    );
    barGroups.add(val);
    i += 1;
    });
    setState(() {
      is_loaded = true;
    });
  }



  @override
  Widget build(BuildContext context) {
    return 
     !is_loaded ? CircularProgressIndicator() :
    Column( crossAxisAlignment: CrossAxisAlignment.stretch,
    children : [ 
     DataTable(
      columns: <DataColumn>[
        DataColumn(
          label: Text(
            'Bird Name',
            style: TextStyle(fontStyle: FontStyle.italic, fontWeight: FontWeight.bold),
          ),
        ),
        DataColumn(
          label: Text(
            'Count',
            style: TextStyle(fontStyle: FontStyle.italic, fontWeight: FontWeight.bold),
          ),
        ),
      ],
      rows: rows,
      ),
      ],
      );

     
     /*
      BarChart(
      BarChartData(
        barTouchData: barTouchData,
        titlesData: titlesData,
        borderData: borderData,
        barGroups: barGroups,
        gridData: FlGridData(show: false),
        alignment: BarChartAlignment.spaceAround,
        maxY: maxY,
      ),
    ); */
  }

  BarTouchData get barTouchData => BarTouchData(
        enabled: false,
        touchTooltipData: BarTouchTooltipData(
          tooltipBgColor: Colors.transparent,
          tooltipPadding: const EdgeInsets.all(0),
          tooltipMargin: 8,
          getTooltipItem: (
            BarChartGroupData group,
            int groupIndex,
            BarChartRodData rod,
            int rodIndex,
          ) {
            return BarTooltipItem(
              //rod.toY.round().toString(),
              counts[groupIndex].toString(),
              const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            );
          },
        ),
      );

  Widget getTitles(double value, TitleMeta meta) {
    const style = TextStyle(
      color: Color(0xff7589a2),
      fontWeight: FontWeight.bold,
      fontSize: 14,
    );
    String text = labels[value.toInt()];
    return SideTitleWidget(
      axisSide: meta.axisSide,
      space: 4.0,
      child: Text(text, style: style),
    );
  }

  FlTitlesData get titlesData => FlTitlesData(
        show: true,
        bottomTitles: AxisTitles(
          sideTitles: SideTitles(
            showTitles: true,
            reservedSize: 30,
            getTitlesWidget: getTitles,
          ),
        ),
        leftTitles: AxisTitles(
          sideTitles: SideTitles(showTitles: false),
        ),
        topTitles: AxisTitles(
          sideTitles: SideTitles(showTitles: false),
        ),
        rightTitles: AxisTitles(
          sideTitles: SideTitles(showTitles: false),
        ),
      );

  FlBorderData get borderData => FlBorderData(
        show: false,
      );

  final _barsGradient = const LinearGradient(
    colors: [
      Colors.lightBlueAccent,
      Colors.greenAccent,
    ],
    begin: Alignment.bottomCenter,
    end: Alignment.topCenter,
  );

}

class SampleItemListView extends StatefulWidget {
  const SampleItemListView({Key? key}) : super(key: key);

  static const routeName = '/sample_item_list_view';
  @override
  State<StatefulWidget> createState() => BarChartSample3State();
}

class BarChartSample3State extends State<SampleItemListView> {
  @override
  Widget build(BuildContext context) {

    return Scaffold(
      appBar: AppBar(
        title: const Text('BirdNet App (Last 24 Hours)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.restorablePushNamed(context, SettingsView.routeName);
            },
          ),
        ],
      ),
      body: Card(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
        color: Theme.of(context).colorScheme.secondary,
        child: _BarChart(),
      ),
    );
  }
}
