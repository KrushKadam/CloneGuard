from gnani import text_to_speech, speech_to_text

print("========== GNANI VOICE APP ==========")
print("1 = I type text   -> Timbre speaks it (saves reply.wav)")
print("2 = I give a file -> Prisma transcribes it")
choice = input("Choose 1 or 2: ").strip()

if choice == "1":
    text = input("Type anything: ").strip()
    path = text_to_speech(text)
    print("DONE. Audio saved as:", path)

elif choice == "2":
    file = input("Path of audio file: ").strip()
    print("TEXT:", speech_to_text(file))

else:
    print("Pick 1 or 2 only.")