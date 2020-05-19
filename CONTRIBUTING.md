Not much to say. We live dangerously so we don't have tests or anything ¯\\_(ツ)_/¯.

We format the code with `black`.

```console
black -l 110 steamsync.py
```

Other than that, you probably can't make it any worse structure wise, so send a 
PR!

Eventually it would be nice to add other launchers, maybe?


### TODO
Feel free to work on any of these and remove them from the list / submit a PR

- Currently, we are hardcoding the path for Steam and the EGS. I know we can 
  detect the Steam installation location through registry keys (see pysteam).
  Something similar might be possible with the EGS
- Since the switch to using URIs instead of paths (use the `--use-paths` switch 
  for the old behavior), there are no icons by default in the Steam library (with
  paths it will at least pull in the executable's icons). Maybe we can extract
  them somewhere?