# GUNDO360

Türkçe, mobil uyumlu canlı haber portalı. Başlamak için `index.html` dosyasını bir tarayıcıda açın; canlı RSS haberleri için internet bağlantısı gerekir.

Haber akışı Google Haberler RSS kaynaklarından GitHub Actions ile saatte bir alınır ve proje kökündeki `news.json` dosyasına yazılır. Actions iş akışı GitHub Actions sekmesinden elle de çalıştırılabilir. Site yalnızca bu statik JSON dosyasını yükler; dosya erişilemiyorsa varsa önceki haberler yerel önbellekten gösterilir.

Tek dosyalı uygulama; Son Dakika, Türkiye, Siyaset, Spor, Futbol, Teknoloji, Ekonomi ve Dünya akışlarını, aramayı, haber ayrıntılarını, paylaşımı, mobil gezinmeyi ve hatırlanan açık/koyu temayı içerir. Haber metinleri ve görselleri yayıncı RSS akışlarından geldiğinden kullanılabilir içerik kaynağa göre değişebilir; tam haber için özgün yayın bağlantısını açın.
