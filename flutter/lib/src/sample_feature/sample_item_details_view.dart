import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:dio/dio.dart';
import '../globals.dart';
import 'package:just_audio/just_audio.dart';

class SampleItemDetailsView extends StatefulWidget {
  const SampleItemDetailsView({Key? key}) : super(key: key);
  static const routeName = '/sample_item';
  @override
  State<StatefulWidget> createState() => SampleItemDetailsViewState();
}

/// Displays detailed information about a SampleItem.
class SampleItemDetailsViewState extends State<SampleItemDetailsView>{
  final _player = AudioPlayer();
  String image_path = '';
  bool loaded = false;

  void initAsync(String name) async {
    var response;
    try {
      response = await Dio().get(PREFIX + "/details/$name");
    } catch (e) {
      print(e);
      return;
    }
    var details = jsonDecode(response.data);
    print(details);
    if (details.isEmpty) {
      return;
    }
    String file = details[0];
    final duration = await _player.setUrl(PREFIX + "/mp3/$name/$file");
    image_path = PREFIX + "/png/$name/$file";
    if (!loaded) {
      loaded = true;
      setState(() {});
    }
  }

  @override
  void dispose() {
    _player.pause();
    _player.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final String name = ModalRoute.of(context)!.settings.arguments.toString();
    initAsync(name);
    return Scaffold(
      appBar: AppBar(
        title: Text(name),
      ),
      body: Center(
        child: Column(
            //crossAxisAlignment: CrossAxisAlignment.center,
            //mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Display play/pause button and volume/speed sliders.
              ControlButtons(_player),

          Flexible( child:
              !loaded ? CircularProgressIndicator() : Image.network(image_path, fit: BoxFit.scaleDown),
              ),
            ],
          ),
      ),
    );
  }
}
/// Displays the play/pause button and volume/speed sliders.
class ControlButtons extends StatelessWidget {
  final AudioPlayer player;

  const ControlButtons(this.player, {Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Opens volume slider dialog
        IconButton(
          icon: const Icon(Icons.volume_up),
          onPressed: () {
            showSliderDialog(
              context: context,
              title: "Adjust volume",
              divisions: 10,
              min: 0.0,
              max: 1.0,
              value: player.volume,
              stream: player.volumeStream,
              onChanged: player.setVolume,
            );
          },
        ),

        /// This StreamBuilder rebuilds whenever the player state changes, which
        /// includes the playing/paused state and also the
        /// loading/buffering/ready state. Depending on the state we show the
        /// appropriate button or loading indicator.
        StreamBuilder<PlayerState>(
          stream: player.playerStateStream,
          builder: (context, snapshot) {
            final playerState = snapshot.data;
            final processingState = playerState?.processingState;
            final playing = playerState?.playing;
            if (processingState == ProcessingState.loading ||
                processingState == ProcessingState.buffering) {
              return Container(
                margin: const EdgeInsets.all(8.0),
                width: 64.0,
                height: 64.0,
                child: const CircularProgressIndicator(),
              );
            } else if (playing != true) {
              return IconButton(
                icon: const Icon(Icons.play_arrow),
                iconSize: 64.0,
                onPressed: player.play,
              );
            } else if (processingState != ProcessingState.completed) {
              return IconButton(
                icon: const Icon(Icons.pause),
                iconSize: 64.0,
                onPressed: player.pause,
              );
            } else {
              return IconButton(
                icon: const Icon(Icons.replay),
                iconSize: 64.0,
                onPressed: () => player.seek(Duration.zero),
              );
            }
          },
        ),
        // Opens speed slider dialog
        StreamBuilder<double>(
          stream: player.speedStream,
          builder: (context, snapshot) => IconButton(
            icon: Text("${snapshot.data?.toStringAsFixed(1)}x",
                style: const TextStyle(fontWeight: FontWeight.bold)),
            onPressed: () {
              showSliderDialog(
                context: context,
                title: "Adjust speed",
                divisions: 10,
                min: 0.5,
                max: 1.5,
                value: player.speed,
                stream: player.speedStream,
                onChanged: player.setSpeed,
              );
            },
          ),
        ),
      ],
    );
  }
}

void showSliderDialog({
  required BuildContext context,
  required String title,
  required int divisions,
  required double min,
  required double max,
  String valueSuffix = '',
  // TODO: Replace these two by ValueStream.
  required double value,
  required Stream<double> stream,
  required ValueChanged<double> onChanged,
}) {
  showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title, textAlign: TextAlign.center),
      content: StreamBuilder<double>(
        stream: stream,
        builder: (context, snapshot) => SizedBox(
          height: 100.0,
          child: Column(
            children: [
              Text('${snapshot.data?.toStringAsFixed(1)}$valueSuffix',
                  style: const TextStyle(
                      fontFamily: 'Fixed',
                      fontWeight: FontWeight.bold,
                      fontSize: 24.0)),
              Slider(
                divisions: divisions,
                min: min,
                max: max,
                value: snapshot.data ?? value,
                onChanged: onChanged,
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
