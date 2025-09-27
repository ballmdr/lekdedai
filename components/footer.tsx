import Link from "next/link"

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">หวย</span>
              </div>
              <span className="font-bold text-xl">สูตรคำนวณหวย</span>
            </div>
            <p className="text-gray-400 mb-4">
              ระบบคำนวณหวยอัจฉริยะที่ช่วยให้คุณวิเคราะห์และทำนายเลขหวยได้อย่างแม่นยำ ด้วยสูตรคำนวณที่ได้รับการพัฒนาและทดสอบมาอย่างดี
            </p>
            <p className="text-sm text-gray-500">* ข้อมูลและการทำนายเป็นเพียงการอ้างอิงเท่านั้น ไม่รับประกันผลลัพธ์</p>
          </div>

          <div>
            <h3 className="font-semibold mb-4">เมนูหลัก</h3>
            <ul className="space-y-2 text-gray-400">
              <li>
                <Link href="/" className="hover:text-white transition-colors">
                  หน้าแรก
                </Link>
              </li>
              <li>
                <Link href="/calculator" className="hover:text-white transition-colors">
                  คำนวณ
                </Link>
              </li>
              <li>
                <Link href="/results" className="hover:text-white transition-colors">
                  ผลการทำนาย
                </Link>
              </li>
              <li>
                <Link href="/statistics" className="hover:text-white transition-colors">
                  สถิติ
                </Link>
              </li>
              <li>
                <Link href="/history" className="hover:text-white transition-colors">
                  ประวัติ
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">ข้อมูล</h3>
            <ul className="space-y-2 text-gray-400">
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  วิธีใช้งาน
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  เกี่ยวกับเรา
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  ติดต่อเรา
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  นโยบายความเป็นส่วนตัว
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2025 สูตรคำนวณหวย. สงวนลิขสิทธิ์.</p>
        </div>
      </div>
    </footer>
  )
}
