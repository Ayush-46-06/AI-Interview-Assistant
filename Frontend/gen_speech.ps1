Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile("test_speech.wav")
$synth.Speak("Hello, this is a test of the speech recognition system for my interview.")
$synth.Dispose()
