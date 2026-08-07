import os
import sys
import time
from datetime import datetime

# Path sozlash
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database
from src.ai_engine import AIEngine
from src.dashboard import Dashboard
from src.speaking import SpeakingModule
from src.writing import WritingModule
from src.reading import ReadingModule
from src.listening import ListeningModule
from src.vocabulary import VocabularyModule
from src.telegram_loader import TelegramLoader
from config.settings import APP_NAME, APP_TAGLINE, USER_NAME

class IFAMentor:
    def __init__(self):
        print("\n⏳ IFA Mentor yuklanmoqda...")
        self._splash_screen()

        # Modullar
        self.db = Database()
        self.ai = AIEngine(self.db)
        self.dashboard = Dashboard(self.db, self.ai)
        self.speaking = SpeakingModule(self.db, self.ai)
        self.writing = WritingModule(self.db, self.ai)
        self.reading = ReadingModule(self.db, self.ai)
        self.listening = ListeningModule(self.db, self.ai)
        self.vocabulary = VocabularyModule(self.db, self.ai)
        self.telegram = TelegramLoader(self.db)

        print(f"\n✅ Barcha modullar yuklandi!")
        print(f"👋 Xush kelibsiz, {USER_NAME}!\n")

    # ─── SPLASH SCREEN ──────────────────────────────────────

    def _splash_screen(self):
        """Terminal splash screen"""
        frames = [
            """
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║         •                            ║
    ║                                      ║
    ╚══════════════════════════════════════╝""",
            """
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║         🧠                           ║
    ║                                      ║
    ╚══════════════════════════════════════╝""",
            """
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║      📖  🧠  🎧                      ║
    ║         🧬                           ║
    ╚══════════════════════════════════════╝""",
            """
    ╔══════════════════════════════════════╗
    ║   📖      🎧                         ║
    ║      🧠  ━━━  🎤                     ║
    ║   ✍️     🧬    Aa                    ║
    ╚══════════════════════════════════════╝""",
            f"""
    ╔══════════════════════════════════════╗
    ║   📖      🎧                         ║
    ║      🧠  ━━━  🎤                     ║
    ║   ✍️     🧬    Aa                    ║
    ║                                      ║
    ║         IFA MENTOR                   ║
    ╚══════════════════════════════════════╝""",
            f"""
    ╔══════════════════════════════════════╗
    ║   📖      🎧                         ║
    ║      🧠  ━━━  🎤                     ║
    ║   ✍️     🧬    Aa                    ║
    ║                                      ║
    ║         IFA MENTOR                   ║
    ║   A personal AI mentor that          ║
    ║   studies you before it teaches you  ║
    ╚══════════════════════════════════════╝"""
        ]

        os.system("cls" if os.name == "nt" else "clear")
        for frame in frames:
            os.system("cls" if os.name == "nt" else "clear")
            print(frame)
            time.sleep(0.4)

    # ─── ASOSIY MENYU ───────────────────────────────────────

    def run(self):
        """Asosiy dastur tsikli"""

        # Kunlik plan yaratish
        today_plan = self.db.get_today_plan()
        if not today_plan:
            self.dashboard.generate_today_plan()

        while True:
            try:
                self.dashboard.show_terminal_dashboard()
                command = input("\n> Buyruq: ").strip().lower()
                self._handle_command(command)

            except KeyboardInterrupt:
                self._exit()
                break
            except Exception as e:
                print(f"\n❌ Xato: {e}")
                print("Davom etish uchun Enter bosing...")
                input()

    # ─── BUYRUQLAR ──────────────────────────────────────────

    def _handle_command(self, command):
        os.system("cls" if os.name == "nt" else "clear")

        # ── DASHBOARD ──
        if command in ["", "d", "dashboard"]:
            self.dashboard.show_terminal_dashboard()

        # ── PLAN ──
        elif command in ["plan", "p"]:
            self._show_plan_menu()

        # ── SPEAKING ──
        elif command in ["speaking", "s", "speak"]:
            self._speaking_menu()

        # ── WRITING ──
        elif command in ["writing", "w", "write"]:
            self._writing_menu()

        # ── READING ──
        elif command in ["reading", "r", "read"]:
            self._reading_menu()

        # ── LISTENING ──
        elif command in ["listening", "l", "listen"]:
            self._listening_menu()

        # ── VOCABULARY ──
        elif command in ["vocabulary", "vocab", "v"]:
            self._vocabulary_menu()

        # ── TELEGRAM ──
        elif command in ["telegram", "sync", "t"]:
            self._telegram_menu()

        # ── STATS ──
        elif command in ["stats", "statistics"]:
            self._show_stats()

        # ── REPORT ──
        elif command in ["report", "weekly"]:
            self.dashboard.generate_weekly_report()
            input("\n[Enter] davom etish...")

        # ── AI CHAT ──
        elif command in ["chat", "ai", "c"]:
            self._ai_chat()

        # ── MOCK ──
        elif command in ["mock", "exam", "m"]:
            self._mock_exam_menu()

        # ── HELP ──
        elif command in ["help", "h", "?"]:
            self._show_help()

        # ── EXIT ──
        elif command in ["exit", "quit", "q"]:
            self._exit()
            sys.exit(0)

        else:
            print(f"❓ Noma'lum buyruq: '{command}'")
            print("   'help' yozing — buyruqlar ro'yxati")
            time.sleep(1.5)

    # ─── PLAN MENYU ─────────────────────────────────────────

    def _show_plan_menu(self):
        print("\n📅 KUNLIK PLAN")
        print("─" * 40)
        print("1. Bugungi planni ko'rish")
        print("2. Yangi plan yaratish (AI)")
        print("3. Ortga")

        choice = input("\nTanlang (1-3): ").strip()

        if choice == "1":
            plan = self.db.get_today_plan()
            if plan:
                print("\n📋 Bugungi vazifalar:")
                total_min = 0
                for i, task in enumerate(plan, 1):
                    status = "✅" if task.get("is_completed") else "⬜"
                    print(f"  {i}. {status} {task['skill']:12} "
                          f"{task['duration_minutes']} min "
                          f"— {task['task_type']}")
                    total_min += task["duration_minutes"]
                print(f"\n  Jami: {total_min} daqiqa")
            else:
                print("❌ Plan yo'q")
            input("\n[Enter] davom etish...")

        elif choice == "2":
            self.dashboard.generate_today_plan()
            input("\n[Enter] davom etish...")

    # ─── SPEAKING MENYU ─────────────────────────────────────

    def _speaking_menu(self):
        print("\n🎤 SPEAKING")
        print("─" * 40)
        print("1. Part 1 mashq (Personal questions)")
        print("2. Part 2 mashq (Image description)")
        print("3. Part 3 mashq (Argumentative)")
        print("4. Mock imtihon (Part 1+2+3)")
        print("5. Tavsiyalarni ko'rish")
        print("6. Ortga")

        choice = input("\nTanlang (1-6): ").strip()

        if choice == "1":
            self.speaking.run_practice_session("Part1")
        elif choice == "2":
            self.speaking.run_practice_session("Part2")
        elif choice == "3":
            self.speaking.run_practice_session("Part3")
        elif choice == "4":
            confirm = input(
                "⚠️  Mock imtihon ~30 daqiqa. Davom etasizmi? (y/n): "
            )
            if confirm.lower() == "y":
                self.speaking.run_mock_exam()
        elif choice == "5":
            tips = self.speaking.get_improvement_tips()
            print(f"\n💡 Tavsiyalar:\n{tips}")

        if choice in ["1", "2", "3", "4", "5"]:
            input("\n[Enter] davom etish...")

    # ─── WRITING MENYU ──────────────────────────────────────

    def _writing_menu(self):
        print("\n✍️  WRITING")
        print("─" * 40)
        print("1. Formal Letter (150+ so'z)")
        print("2. Argumentative Essay (250+ so'z)")
        print("3. Mock imtihon (Letter + Essay)")
        print("4. O'tgan esseylarni ko'rish")
        print("5. Mavzu bo'yicha vocabulary")
        print("6. Tavsiyalarni ko'rish")
        print("7. Ortga")

        choice = input("\nTanlang (1-7): ").strip()

        if choice == "1":
            self.writing.run_practice_session("formal_letter")
        elif choice == "2":
            self.writing.run_practice_session("argumentative_essay")
        elif choice == "3":
            confirm = input(
                "⚠️  Mock imtihon ~70 daqiqa. Davom etasizmi? (y/n): "
            )
            if confirm.lower() == "y":
                self.writing.run_mock_exam()
        elif choice == "4":
            self.writing.analyze_past_essays()
        elif choice == "5":
            topic = input("Mavzu: ").strip()
            vocab = self.writing.get_writing_vocabulary(topic)
            if "error" not in vocab:
                print("\n📚 Linking words:")
                for category, words in vocab.get(
                        "linking_words", {}).items():
                    print(f"  {category}: {', '.join(words)}")
                print("\n💬 Useful phrases:")
                for phrase in vocab.get("useful_phrases", [])[:5]:
                    print(f"  • {phrase}")
        elif choice == "6":
            tips = self.writing.get_improvement_tips()
            print(f"\n💡 Tavsiyalar:\n{tips}")

        if choice in ["1", "2", "3", "4", "5", "6"]:
            input("\n[Enter] davom etish...")

    # ─── READING MENYU ──────────────────────────────────────

    def _reading_menu(self):
        print("\n📖 READING")
        print("─" * 40)
        print("1. B2 mashq (Part 3+4)")
        print("2. Zaif partlarni mashq qilish")
        print("3. Mock imtihon (35 savol, 6 part)")
        print("4. Tavsiyalarni ko'rish")
        print("5. Ortga")

        choice = input("\nTanlang (1-5): ").strip()

        if choice == "1":
            self.reading.run_b2_practice()
        elif choice == "2":
            self.reading.run_weak_parts()
        elif choice == "3":
            confirm = input(
                "⚠️  Mock imtihon ~60 daqiqa. Davom etasizmi? (y/n): "
            )
            if confirm.lower() == "y":
                self.reading.run_mock_exam()
        elif choice == "4":
            tips = self.reading.get_improvement_tips()
            print(f"\n💡 Tavsiyalar:\n{tips}")

        if choice in ["1", "2", "3", "4"]:
            input("\n[Enter] davom etish...")

    # ─── LISTENING MENYU ────────────────────────────────────

    def _listening_menu(self):
        print("\n🎧 LISTENING")
        print("─" * 40)
        print("1. B2 mashq (Part 3+4)")
        print("2. Zaif partlarni mashq qilish")
        print("3. Mock imtihon (30 savol, 6 part)")
        print("4. Tavsiyalarni ko'rish")
        print("5. Ortga")

        choice = input("\nTanlang (1-5): ").strip()

        if choice == "1":
            self.listening.run_b2_practice()
        elif choice == "2":
            self.listening.run_weak_parts()
        elif choice == "3":
            confirm = input(
                "⚠️  Mock imtihon ~40 daqiqa. Davom etasizmi? (y/n): "
            )
            if confirm.lower() == "y":
                self.listening.run_mock_exam()
        elif choice == "4":
            tips = self.listening.get_improvement_tips()
            print(f"\n💡 Tavsiyalar:\n{tips}")

        if choice in ["1", "2", "3", "4"]:
            input("\n[Enter] davom etish...")

    # ─── VOCABULARY MENYU ───────────────────────────────────

    def _vocabulary_menu(self):
        print("\n📚 VOCABULARY")
        print("─" * 40)
        print("1. Kunlik takrorlash (Spaced Repetition)")
        print("2. Yangi so'z qo'shish")
        print("3. Bugungi so'z (Word of the Day)")
        print("4. Statistika")
        print("5. Tavsiyalar")
        print("6. Ortga")

        choice = input("\nTanlang (1-6): ").strip()

        if choice == "1":
            self.vocabulary.run_review_session()
        elif choice == "2":
            word = input("So'z: ").strip()
            uzbek = input("O'zbekcha (ixtiyoriy): ").strip()
            if word:
                result = self.vocabulary.add_word_manual(word, uzbek)
                if result:
                    print(f"\n✅ {result.get('word')} → "
                          f"{result.get('uzbek')}")
                    print(f"📖 {result.get('definition')}")
                    print(f"💬 {result.get('example_ai')}")
        elif choice == "3":
            word = self.vocabulary.get_word_of_day()
            print(f"\n🌟 BUGUNGI SO'Z")
            print(f"   {word.get('word', '')} "
                  f"[{word.get('pronunciation', '')}]")
            print(f"   🇺🇿 {word.get('uzbek', '')}")
            print(f"   📖 {word.get('definition', '')}")
            print(f"   💬 {word.get('example_ai', word.get('example', ''))}")
        elif choice == "4":
            self.vocabulary.show_stats()
        elif choice == "5":
            tips = self.vocabulary.get_improvement_tips()
            print(f"\n💡 {tips}")

        if choice in ["1", "2", "3", "4", "5"]:
            input("\n[Enter] davom etish...")

    # ─── TELEGRAM MENYU ─────────────────────────────────────

    def _telegram_menu(self):
        print("\n📡 TELEGRAM")
        print("─" * 40)
        print("1. Barcha kanallarni sinxronlash")
        print("2. Yangi kanal qo'shish")
        print("3. Kanallar ro'yxati")
        print("4. Material statistikasi")
        print("5. Qo'lda fayl qo'shish")
        print("6. Ortga")

        choice = input("\nTanlang (1-6): ").strip()

        if choice == "1":
            print("\n🔄 Sinxronlanmoqda...")
            self.telegram.sync()

        elif choice == "2":
            print("\n📌 Yangi kanal qo'shish")
            print("Misol: @multilevel_english")
            channel_name = input("Kanal nomi (@...): ").strip()
            channel_id = input("Kanal ID: ").strip()
            print("\nSkill tanlang:")
            print("1. listening  2. reading  3. writing")
            print("4. speaking   5. vocabulary  6. mixed")
            skill_map = {
                "1": "listening", "2": "reading",
                "3": "writing", "4": "speaking",
                "5": "vocabulary", "6": "mixed"
            }
            skill_choice = input("Tanlang (1-6): ").strip()
            skill = skill_map.get(skill_choice, "mixed")
            self.telegram.add_channel(channel_name, channel_id, skill)

        elif choice == "3":
            channels = self.db.get_active_channels()
            if channels:
                print("\n📋 Kanallar:")
                for ch in channels:
                    print(f"  {ch['channel_name']:25} "
                          f"→ {ch['skill']:12} "
                          f"({ch['total_materials']} material)")
            else:
                print("❌ Hech qanday kanal yo'q")

        elif choice == "4":
            self.telegram.get_stats()

        elif choice == "5":
            file_path = input("Fayl yo'li: ").strip()
            print("Skill: 1.listening 2.reading 3.writing 4.speaking")
            skill_map = {
                "1": "listening", "2": "reading",
                "3": "writing", "4": "speaking"
            }
            s = input("Tanlang (1-4): ").strip()
            skill = skill_map.get(s, "reading")
            self.telegram.add_manual_material(file_path, skill)

        input("\n[Enter] davom etish...")

    # ─── STATISTIKA ─────────────────────────────────────────

    def _show_stats(self):
        print("\n📊 TO'LIQ STATISTIKA")
        print("═" * 50)

        # Har bir skill statistikasi
        modules = [
            ("Speaking",   self.speaking.get_speaking_stats),
            ("Writing",    self.writing.get_writing_stats),
            ("Reading",    self.reading.get_reading_stats),
            ("Listening",  self.listening.get_listening_stats)
        ]

        for name, get_stats in modules:
            stats = get_stats()
            total = stats.get("total_sessions", 0)
            avg = stats.get("avg_score") or stats.get(
                "avg_percentage", 0)
            best = stats.get("best_score") or stats.get("best", 0)
            print(f"\n{name}:")
            print(f"  Jami sessiyalar: {total}")
            if total > 0:
                print(f"  O'rtacha ball:   {round(avg or 0, 1)}")
                print(f"  Eng yaxshi:      {round(best or 0, 1)}")

        # Vocabulary
        vocab_stats = self.vocabulary.get_vocabulary_stats()
        print(f"\nVocabulary:")
        print(f"  Jami so'zlar:    {vocab_stats['total_words']}")
        print(f"  O'zlashtirilgan: {vocab_stats['mastered']}")
        print(f"  O'rganilmoqda:   {vocab_stats['learning']}")

        # Progress tahlil
        analysis = self.dashboard.get_progress_analysis()
        overall = analysis.get("overall", {})
        print(f"\n{'─' * 50}")
        print(f"B2 ga qoldi:    {overall.get('gap', 0)} ball")
        print(f"Taxminiy sana:  {overall.get('eta', 'N/A')}")
        print("═" * 50)
        input("\n[Enter] davom etish...")

    # ─── AI CHAT ────────────────────────────────────────────

    def _ai_chat(self):
        print("\n🤖 AI CHAT")
        print("─" * 40)
        print("IFA Mentor AI bilan suhbat")
        print("Chiqish uchun: 'exit' yozing")
        print("─" * 40)

        self.ai.clear_history()

        while True:
            try:
                user_input = input(f"\n{USER_NAME}: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    break

                print("\n🤖 IFA Mentor: ", end="", flush=True)
                response = self.ai.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                break

        print("\n✅ Chat yakunlandi")
        input("[Enter] davom etish...")

    # ─── MOCK IMTIHON MENYU ─────────────────────────────────

    def _mock_exam_menu(self):
        print("\n🎓 MOCK IMTIHON")
        print("─" * 40)
        print("1. Speaking Mock  (~30 min)")
        print("2. Writing Mock   (~70 min)")
        print("3. Reading Mock   (~60 min)")
        print("4. Listening Mock (~40 min)")
        print("5. To'liq Mock    (~3.5 soat)")
        print("6. Ortga")

        choice = input("\nTanlang (1-6): ").strip()

        if choice == "1":
            self.speaking.run_mock_exam()
        elif choice == "2":
            self.writing.run_mock_exam()
        elif choice == "3":
            self.reading.run_mock_exam()
        elif choice == "4":
            self.listening.run_mock_exam()
        elif choice == "5":
            confirm = input(
                "⚠️  To'liq mock ~3.5 soat. Davom etasizmi? (y/n): "
            )
            if confirm.lower() == "y":
                self._run_full_mock()

        if choice in ["1", "2", "3", "4", "5"]:
            input("\n[Enter] davom etish...")

    def _run_full_mock(self):
        """To'liq mock imtihon"""
        print("\n🎓 TO'LIQ MOCK IMTIHON BOSHLANDI")
        print("Sana:", datetime.now().strftime("%d.%m.%Y %H:%M"))
        print("═" * 50)

        results = {}
        order = [
            ("Listening", self.listening.run_mock_exam),
            ("Reading",   self.reading.run_mock_exam),
            ("Writing",   self.writing.run_mock_exam),
            ("Speaking",  self.speaking.run_mock_exam)
        ]

        for skill, run_mock in order:
            print(f"\n━━━ {skill.upper()} ━━━")
            input(f"[Enter] {skill} ni boshlash...")
            result = run_mock()
            if result:
                results[skill] = result

        # Yakuniy natija
        print("\n" + "═" * 50)
        print("🏆 TO'LIQ MOCK NATIJASI")
        print("═" * 50)
        for skill, result in results.items():
            if "overall_percentage" in result:
                print(f"  {skill:12}: "
                      f"{result['overall_percentage']}%")
            elif "overall" in result:
                print(f"  {skill:12}: {result['overall']}")
        print("═" * 50)

    # ─── HELP ───────────────────────────────────────────────

    def _show_help(self):
        print("""
╔══════════════════════════════════════════╗
║           IFA MENTOR — BUYRUQLAR         ║
╠══════════════════════════════════════════╣
║  d / dashboard  → Asosiy ekran           ║
║  p / plan       → Kunlik plan            ║
║  s / speaking   → Speaking mashq         ║
║  w / writing    → Writing mashq          ║
║  r / reading    → Reading mashq          ║
║  l / listening  → Listening mashq        ║
║  v / vocab      → Vocabulary             ║
║  t / telegram   → Telegram kanallar      ║
║  m / mock       → Mock imtihon           ║
║  c / chat       → AI bilan suhbat        ║
║  stats          → To'liq statistika      ║
║  report         → Haftalik hisobot       ║
║  q / exit       → Chiqish                ║
╚══════════════════════════════════════════╝""")
        input("\n[Enter] davom etish...")

    # ─── CHIQISH ────────────────────────────────────────────

    def _exit(self):
        print(f"""
╔══════════════════════════════════════════╗
║                                          ║
║   Xayr, {USER_NAME}! 👋                      
║   Bugun ham zo'r ishlading!              ║
║                                          ║
║   B2 ga: har kun bir qadam! 🎯           ║
║                                          ║
╚══════════════════════════════════════════╝""")
        time.sleep(1.5)


# ─── ISHGA TUSHIRISH ────────────────────────────────────────

if __name__ == "__main__":
    app = IFAMentor()
    app.run()