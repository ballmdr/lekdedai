import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Brain,
  TrendingUp,
  Newspaper,
  Moon,
  Search,
  Zap,
  BarChart3,
  Trophy,
  Calendar,
  Clock,
  Star,
  Users,
  MapPin,
  Navigation,
} from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-primary-foreground" />
              </div>
              <h1 className="text-xl font-serif font-bold text-foreground">เลขเด็ดเอไอ</h1>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <a href="#today" className="text-muted-foreground hover:text-foreground transition-colors">
                เลขวันนี้
              </a>
              <a href="#statistics" className="text-muted-foreground hover:text-foreground transition-colors">
                สถิติ
              </a>
              <a href="#news" className="text-muted-foreground hover:text-foreground transition-colors">
                ข่าวหวย
              </a>
              <a href="#dreams" className="text-muted-foreground hover:text-foreground transition-colors">
                ความฝัน
              </a>
              <a href="#locations" className="text-muted-foreground hover:text-foreground transition-colors">
                พิกัดเลขเด็ด
              </a>
              <a href="#check" className="text-muted-foreground hover:text-foreground transition-colors">
                ตรวจหวย
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Daily Content Hero */}
      <section className="py-12 bg-gradient-to-br from-primary/5 via-background to-secondary/5 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,193,7,0.1),transparent_50%)]"></div>

        <div className="container mx-auto px-4 relative z-10">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Calendar className="w-5 h-5 text-primary" />
              <span className="text-sm font-medium text-muted-foreground">
                วันที่{" "}
                {new Date().toLocaleDateString("th-TH", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-serif font-bold text-foreground mb-4">เลขเด็ดประจำวัน</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">อัปเดตเลขเด็ด ข่าวหวย และสถิติล่าสุดทุกวัน</p>
          </div>

          {/* Today's Featured Numbers */}
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader className="text-center pb-2">
                <CardTitle className="text-lg font-serif">เลขเด็ด AI</CardTitle>
                <Badge className="bg-primary text-primary-foreground mx-auto">
                  <Star className="w-3 h-3 mr-1" />
                  แนะนำ
                </Badge>
              </CardHeader>
              <CardContent className="text-center">
                <div className="text-3xl font-bold text-primary mb-2">4 2 7</div>
                <div className="text-sm text-muted-foreground">ความแม่นยำ 87%</div>
              </CardContent>
            </Card>

            <Card className="border-secondary/20 bg-secondary/5">
              <CardHeader className="text-center pb-2">
                <CardTitle className="text-lg font-serif">เลขฮิต</CardTitle>
                <Badge variant="secondary" className="mx-auto">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  ยอดนิยม
                </Badge>
              </CardHeader>
              <CardContent className="text-center">
                <div className="text-3xl font-bold text-secondary mb-2">1 5</div>
                <div className="text-sm text-muted-foreground">ออกบ่อย 15 ครั้ง</div>
              </CardContent>
            </Card>

            <Card className="border-accent/20 bg-accent/5">
              <CardHeader className="text-center pb-2">
                <CardTitle className="text-lg font-serif">เลขเสริมดวง</CardTitle>
                <Badge variant="outline" className="mx-auto">
                  <Moon className="w-3 h-3 mr-1" />
                  จากความฝัน
                </Badge>
              </CardHeader>
              <CardContent className="text-center">
                <div className="text-3xl font-bold text-accent mb-2">8 9</div>
                <div className="text-sm text-muted-foreground">ฝันเห็นงู</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Daily Stats & Quick Info */}
      <section className="py-8 bg-card/30">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-primary mb-1">1,247</div>
              <div className="text-sm text-muted-foreground">คนเข้าชมวันนี้</div>
            </div>
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-secondary mb-1">89%</div>
              <div className="text-sm text-muted-foreground">ความแม่นยำเฉลี่ย</div>
            </div>
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-accent mb-1">156</div>
              <div className="text-sm text-muted-foreground">เลขที่ทำนายแล้ว</div>
            </div>
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-primary mb-1">24</div>
              <div className="text-sm text-muted-foreground">ข่าวใหม่วันนี้</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Sections */}
      <section className="py-16" id="today">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Left Column - Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Latest Lottery News */}
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-serif font-bold text-foreground flex items-center gap-2">
                    <Newspaper className="w-6 h-6 text-primary" />
                    ข่าวหวยล่าสุด
                  </h3>
                  <Button variant="outline" size="sm">
                    ดูทั้งหมด
                  </Button>
                </div>

                <div className="space-y-4">
                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex gap-4">
                        <div className="w-16 h-16 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Newspaper className="w-8 h-8 text-primary" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-2">อุบัติเหตุรถชนที่สะพานพระราม 4 ทะเบียน กข-1234</h4>
                          <p className="text-sm text-muted-foreground mb-2">เหตุการณ์เกิดขึ้นเมื่อเช้านี้ ใบ้เลขเด็ด 12, 34, 56</p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />2 ชั่วโมงที่แล้ว
                            </span>
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              อ่าน 1,234 ครั้ง
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex gap-4">
                        <div className="w-16 h-16 bg-secondary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Trophy className="w-8 h-8 text-secondary" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-2">ผลหวยงวดที่แล้ว เลขท้าย 2 ตัว "15" ออกแล้ว!</h4>
                          <p className="text-sm text-muted-foreground mb-2">
                            AI ของเราทำนายถูก เลขท้าย 2 ตัว งวดวันที่ 16 ธันวาคม 2567
                          </p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />5 ชั่วโมงที่แล้ว
                            </span>
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              อ่าน 2,567 ครั้ง
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              {/* Lottery Locations */}
              <div id="locations">
                <h3 className="text-2xl font-serif font-bold text-foreground mb-6 flex items-center gap-2">
                  <MapPin className="w-6 h-6 text-primary" />
                  พิกัดเลขเด็ด - สถานที่ขอหวย
                </h3>

                <div className="grid md:grid-cols-2 gap-4">
                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex gap-4">
                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <MapPin className="w-6 h-6 text-primary" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-1">วัดไผ่ล้อม</h4>
                          <p className="text-sm text-muted-foreground mb-2">วัดดังขอเลขเด็ด เลขที่ออกบ่อย: 27, 72, 07</p>
                          <div className="flex items-center justify-between">
                            <Badge variant="outline" className="text-xs">
                              <Star className="w-3 h-3 mr-1" />
                              ยอดนิยม
                            </Badge>
                            <Button variant="ghost" size="sm" className="text-xs">
                              <Navigation className="w-3 h-3 mr-1" />
                              นำทาง
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex gap-4">
                        <div className="w-12 h-12 bg-secondary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <MapPin className="w-6 h-6 text-secondary" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-1">ศาลเจ้าพ่อหลักเมือง</h4>
                          <p className="text-sm text-muted-foreground mb-2">ศาลเจ้าศักดิ์สิทธิ์ เลขแนะนำ: 89, 98, 19</p>
                          <div className="flex items-center justify-between">
                            <Badge variant="secondary" className="text-xs">
                              <Trophy className="w-3 h-3 mr-1" />
                              แม่นยำสูง
                            </Badge>
                            <Button variant="ghost" size="sm" className="text-xs">
                              <Navigation className="w-3 h-3 mr-1" />
                              นำทาง
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex gap-4">
                        <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <MapPin className="w-6 h-6 text-accent" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-1">วัดพระแก้ว</h4>
                          <p className="text-sm text-muted-foreground mb-2">วัดหลวงในกรุงเทพฯ เลขมงคล: 01, 10, 11</p>
                          <div className="flex items-center justify-between">
                            <Badge variant="outline" className="text-xs">
                              <Moon className="w-3 h-3 mr-1" />
                              ศักดิ์สิทธิ์
                            </Badge>
                            <Button variant="ghost" size="sm" className="text-xs">
                              <Navigation className="w-3 h-3 mr-1" />
                              นำทาง
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex gap-4">
                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <MapPin className="w-6 h-6 text-primary" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-1">ศาลหลักเมืองเชียงใหม่</h4>
                          <p className="text-sm text-muted-foreground mb-2">ศาลประจำจังหวัด เลขเด่น: 56, 65, 05</p>
                          <div className="flex items-center justify-between">
                            <Badge variant="outline" className="text-xs">
                              <Users className="w-3 h-3 mr-1" />
                              คนนิยม
                            </Badge>
                            <Button variant="ghost" size="sm" className="text-xs">
                              <Navigation className="w-3 h-3 mr-1" />
                              นำทาง
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div className="mt-6 text-center">
                  <Button variant="outline">
                    <MapPin className="w-4 h-4 mr-2" />
                    ดูพิกัดเลขเด็ดทั้งหมด
                  </Button>
                </div>
              </div>

              {/* Dream Interpretation */}
              <div>
                <h3 className="text-2xl font-serif font-bold text-foreground mb-6 flex items-center gap-2">
                  <Moon className="w-6 h-6 text-primary" />
                  แปลความฝันวันนี้
                </h3>

                <Card>
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      <div className="bg-muted/50 p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">ความฝันยอดนิยม: "ฝันเห็นงูใหญ่สีเขียว"</h4>
                        <p className="text-sm text-muted-foreground mb-3">
                          งูสีเขียวในความฝันแทนความโชคดีและเงินทอง แนะนำเลข 89, 98, 08
                        </p>
                        <div className="flex gap-2">
                          <Badge variant="outline">89</Badge>
                          <Badge variant="outline">98</Badge>
                          <Badge variant="outline">08</Badge>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <Textarea placeholder="เล่าความฝันของคุณ..." rows={3} className="resize-none" />
                        <Button className="w-full">
                          <Moon className="w-4 h-4 mr-2" />
                          แปลความฝันของฉัน
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="space-y-6">
              {/* Quick Lottery Check */}
              <Card>
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <Search className="w-5 h-5 text-primary" />
                    ตรวจหวยด่วน
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Input placeholder="กรอกเลข 6 หลัก" />
                  <Button className="w-full">ตรวจผลหวย</Button>
                  <div className="text-xs text-muted-foreground text-center">งวดล่าสุด: 16 ธ.ค. 2567</div>
                </CardContent>
              </Card>

              {/* Hot Numbers */}
              <Card>
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-secondary" />
                    เลขฮิตประจำสัปดาห์
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">เลขออกบ่อย</span>
                      <div className="flex gap-1">
                        <Badge variant="secondary">07</Badge>
                        <Badge variant="secondary">23</Badge>
                        <Badge variant="secondary">45</Badge>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">เลขไม่เคยออก</span>
                      <div className="flex gap-1">
                        <Badge variant="outline">89</Badge>
                        <Badge variant="outline">91</Badge>
                        <Badge variant="outline">96</Badge>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">เลขแนวโน้มสูง</span>
                      <div className="flex gap-1">
                        <Badge className="bg-accent text-accent-foreground">12</Badge>
                        <Badge className="bg-accent text-accent-foreground">34</Badge>
                        <Badge className="bg-accent text-accent-foreground">56</Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* AI Prediction */}
              <Card className="border-primary/20">
                <CardHeader>
                  <CardTitle className="font-serif flex items-center gap-2">
                    <Brain className="w-5 h-5 text-primary" />
                    AI ทำนายใหม่
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center space-y-4">
                    <div>
                      <div className="text-2xl font-bold text-primary mb-1">4 2 7</div>
                      <div className="text-sm text-muted-foreground">เลขบน 3 ตัว</div>
                      <Badge className="bg-primary/10 text-primary mt-2">87% แม่นยำ</Badge>
                    </div>
                    <Button size="sm" className="w-full">
                      <Zap className="w-4 h-4 mr-2" />
                      สร้างเลขใหม่
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-card border-t border-border py-8">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-primary-foreground" />
                </div>
                <h4 className="font-serif font-bold">เลขเด็ดเอไอ</h4>
              </div>
              <p className="text-sm text-muted-foreground">พอร์ทัลเลขเด็ดและข่าวหวยอันดับ 1 ของไทย</p>
            </div>
            <div>
              <h5 className="font-semibold mb-4">เมนูหลัก</h5>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    เลขเด็ดวันนี้
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    ข่าวหวย
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    สถิติหวย
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    ตรวจหวย
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h5 className="font-semibold mb-4">ติดตาม</h5>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>Facebook: เลขเด็ดเอไอ</li>
                <li>Line: @lekded-ai</li>
                <li>อีเมล: info@lekded-ai.com</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border mt-6 pt-6 text-center text-sm text-muted-foreground">
            <p>&copy; 2024 เลขเด็ดเอไอ - พอร์ทัลเลขเด็ดและข่าวหวย</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
