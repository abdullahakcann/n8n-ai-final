# Kurulum Kılavuzu — Windows Üzerinde n8n Container + Git Hook Pipeline

Bu doküman, elinizdeki dosyaları (`n8n-docker.tar`, `n8n_data.tar.gz`, `aselsan-ca.crt`, `.githooks/`, `cppcheck-2.21.0-x64-Setup.msi`) kullanarak pipeline'ı sıfırdan Windows bilgisayarınızda ayağa kaldırmanız için gereken tüm adımları içerir.

---

## 0. Ön Gereksinimler

| Gereksinim | Not |
|---|---|
| **WSL 2** | Docker Desktop'ın Windows üzerinde çalışabilmesi için zorunludur. |
| **Docker Desktop — 4.48.0 veya daha eski bir sürüm** | Şirketteki çoğu bilgisayar Windows 10 21H2 sürümüne sahip olduğu için bu sürüm önerilmiştir. Docker Desktop 4.49.0 sürümünden itibaren bu Windows sürümünü artık desteklememektedir. Eğer Windows 10 22H2 veya daha yeni bir sürüme sahipseniz, daha yeni bir Docker Desktop sürümü de kullanabilirsiniz.  |
| **Git** | Repo'yu klonlamak ve hook'ları etkinleştirmek için gerekli. |
| Kurulum dosyaları | `n8n-docker.tar`: n8n'in kurulu olduğu Docker container, `n8n_data.tar.gz`: n8n workflowlarını barındıran container datası. `aselsan-ca.crt`: İç ağdaki LLM'ler ile Jira ve Email sunucularına erişim için sertifika, `Cppcheck installer (.exe)`: Statik kod analizi ve misra c standart analizi için gerekli uygulama. `Docker Desktop 4.43.1 installer (.exe)`: Docker Desktop kurulum dosyası.

> WSL kurulum dosyasına ihtiyacınız varsa, "\\\argeds\apps\KURULUM_Arge\AGS_APPS\AGS-ATD\ACYYTM\WSL" klasöründe bulabilirsiniz.

---

## 1. WSL 2'nin Etkinleştirilmesi

PowerShell'i **yönetici olarak** açıp aşağıdaki komutu çalıştırın:

```powershell
wsl --install
```

Bilgisayarınızı yeniden başlatın. WSL zaten kuruluysa bu adımı atlayabilirsiniz. Kurulumu doğrulamak için:

```powershell
wsl --status
```

çıktısında varsayılan sürümün **2** olduğunu görmelisiniz. Eğer WSL 2 kurulu ise ancak varsayılan sürüm **2** değilse aşağıdaki komutla varsayılan sürümü değiştirin.
```powershell
wsl --set-default-version 2
```
---

## 2. Docker Desktop Kurulumu (≤ 4.48.0)

1. `Docker Desktop Installer.exe` kurulum dosyasını çalıştırın (ya da Docker'ın resmi arşivinden 4.48.0 veya öncesi bir sürümü indirin).
2. Kurulum sırasında **"Use WSL 2 instead of Hyper-V"** seçeneğinin işaretli olduğundan emin olun.
3. Kurulum tamamlandıktan sonra Docker Desktop'ı açın ve sağ alttaki motorun (Docker Engine) çalışır durumda olduğunu doğrulayın.
4. Bir terminalde doğrulayın:

```powershell
docker --version
docker ps
```

Hata almadan boş bir konteyner listesi dönüyorsa Docker hazırdır.

---

## 3. n8n İmajının ve Verilerinin Yüklenmesi

Aşağıdaki üç dosyayı bir çalışma klasörüne kopyalayın, örneğin:

```
C:\Users\KullaniciAdi\Desktop\n8n_projesi\
├── n8n-docker.tar
├── n8n_data.tar.gz
└── aselsan-ca.crt
```

### 3.1 Docker imajını yükleyin

PowerShell'de çalışma klasörüne gidin ve imajı yükleyin:

```powershell
cd "C:\Users\KullaniciAdi\Desktop\n8n_projesi"
docker load -i n8n-docker.tar
```
Bu işlem diskinizin hızına göre 3-4 dk sürebilir.

Komut bitince `docker images` ile `n8n-image` adlı imajın listede göründüğünü doğrulayın:

```powershell
docker images
```

### 3.2 Veri yedeğini (workflow'lar, credential'lar) açın

`n8n_data.tar.gz` bir Linux `tar.gz` arşivi olduğu için Windows'ta açmak isterseniz aşağıdaki komut ile veya 7-Zip ile 'Extract Here' yaparak açabilirsiniz. Önerilen yöntem powershell terminalinde aşağıdaki komutu çalıştırmaktır:

```powershell
tar -xzvf n8n_data.tar.gz
```

Bu komut, içinde workflow'ları ve credential'ları barındıran `n8n_data` klasörünü aynı dizine çıkaracaktır. İşlem sonunda klasör yapınız şöyle olmalı:

```
C:\Users\KullaniciAdi\Desktop\n8n_projesi\
├── n8n-docker.tar
├── n8n_data.tar.gz
├── n8n_data\           <-- yeni çıkan klasör
└── aselsan-ca.crt
```

> **Not:** Arşivi doğrudan Windows Explorer üzerinden (sağ tık → çıkart) açarsanız dosya izinleri (permissions) ve gizli dosyalar (`.` ile başlayanlar, örn. `.n8n` config dosyaları) bozulabilir. Yukarıdaki gibi terminal üzerinden `tar` komutuyla açın veya 7-Zip kullanın.

---

## 4. Container'ı Çalıştırma

Aşağıdaki komutu PowerShell'de çalıştırın. Path içindeki `KullaniciAdi` kısmını kendi kullanıcı adınızla değiştirin.

```powershell
docker run -d --name n8n -p 5678:5678 -v "C:\Users\KullaniciAdi\Desktop\n8n_projesi\n8n_data:/home/node/.n8n" -v "C:\Users\KullaniciAdi\Desktop\n8n_projesi\aselsan-ca.crt:/certs/aselsan-ca.crt" -e NODES_EXCLUDE="[]" -e NODE_EXTRA_CA_CERTS="/certs/aselsan-ca.crt" -e NODE_FUNCTION_ALLOW_BUILTIN="fs"  --add-host=host.docker.internal:host-gateway n8n-image
```

Bu komutta:

- `-p 5678:5678` → n8n arayüzünü `http://localhost:5678` üzerinden erişilebilir kılar.
- `-v ...n8n_data:/home/node/.n8n` → az önce açtığınız veri klasörünü (workflow'lar, credential'lar, ayarlar) container'ın içine bağlar.
- `-v ...aselsan-ca.crt:/certs/aselsan-ca.crt` ve `-e NODE_EXTRA_CA_CERTS=...` → şirket içi ağdaki (intranet) servislere erişim için gereken CA sertifikasını container'a tanıtır.

> **Önemli — CA sertifikası hakkında:** İmaj Linux üzerinde derlenirken sertifika imajın içine gömülmüş olsa da, Windows'ta Docker Desktop/WSL2 backend'i container'ı farklı bir şekilde başlattığı için bu sertifika otomatik olarak tanınmıyor. Bu yüzden Windows'ta container'ı **mutlaka** yukarıdaki `-v ...aselsan-ca.crt...` ve `-e NODE_EXTRA_CA_CERTS=...` satırlarıyla birlikte çalıştırmanız gerekiyor; aksi halde intranet servislerine (Jira, dahili LLM sunucusu vb.) yapılan istekler sertifika hatasıyla başarısız olur.

Container'ın ayağa kalktığını doğrulayın:

```powershell
docker ps
```

`n8n` adıyla `Up` durumunda bir satır görmelisiniz.

---

## 5. n8n Arayüzüne Giriş ve Credential'ların Eklenmesi

1. Tarayıcıdan `http://localhost:5678` adresine gidin. Taşınan veri klasörü sayesinde mevcut kullanıcı hesabı ve tüm workflow'lar (main pipeline, Code Quality/Security/Standard Compliance agent'ları, bypass report pipeline) hazır gelecektir.
2. Giriş yaptıktan sonra **her geliştirici kendi credential'larını** `http://localhost:5678/home/credentials` adresinden eklemelidir. (mevcut credential'lar sizin hesap bilgilerinizi içermeyecektir, herkes kendi anahtarlarını eklemelidir):
   - **OpenAI Account:** `https://portal.aiplatform.aselsan.com.tr/api-platform` adresinde sayfayı aşağı kaydırıp `API Key` butonuna basarak API key talebi oluşturun. API anahtarınızı aldıktan sonra `Bearer SIZIN_ASELIXAI_API_ANAHTARINIZ` formatında olacak şekilde kopyalayıp `API Key` ve Authorization headerının `Header Value` alanına yapıştırın. Sağ üstten `Save` tuşuna basın.
   - **Jira SW Server (PAT) account:** Jira hesabınızdan bir **Personal Access Token (PAT)** oluşturup bu token'ı ilgili credential alanına girin ve sağ üstten kaydedin. **Personal Access Token** oluşturmak için Jira hesabınıza giriş yapın, `Profile -> Personal Access Tokens -> Create Token` butonuna tıklayın. Oluşturduğunuz token yalnızca bir kez görüntülenebilecek bu yüzden oluşturduktan sonra n8n credentialını kaydedin. Eğer takımınızın Jira hostname'i farklı ise hem buradan hem de `bypass-report` workflowu içindeki `Set Config` node'u içinden değiştirin.
   - **SMTP Account:** Kendi kurumsal e-posta adresinizi ve şifrenizi girin. `Client Host Name` alanına bilgisayarınızın ağa bağlandığı ip adresini girin. (Örn: 110.13.30.18)
3. Credential'ları kaydettikten sonra workflow'lara tıklayıp sağ üstte `Published` yazdığını doğrulayın, eğer `Publish` tuşu varsa tıklayın.

---

## 6. Git Hook'larının Etkinleştirilmesi

1. `.githooks/` klasörünü, üzerinde çalıştığınız repo'nun **kök dizinine** kopyalayın:

```
<repo-kök-dizini>\
├── .githooks\
│   └── commit-msg
├── src\
└── ...
```

2. Repo dizininde bir terminal açıp Git'e bu klasörü hook dizini olarak kullanmasını söyleyin:

```powershell
cd <repo-kök-dizini>
git config core.hooksPath .githooks/
```

3. Doğrulamak için:

```powershell
git config core.hooksPath
```

çıktısı `.githooks/` olmalı. Bu ayar yalnızca yerel repo klonunuz için geçerlidir, her yeni klonda tekrar ayarlanması gerekir.

---

## 7. Cppcheck Kurulumu

1. Size verilen Cppcheck kurulum dosyasını (`.exe`) çalıştırın.
2. Kurulum sihirbazında **"Python addons"** seçeneğinin işaretli olduğundan emin olun (bu, MISRA addon'unun çalışması için zorunludur). İşaretli değilse etkinleştirin.
3. Kurulumu tamamlayın (varsayılan kurulum yolu genellikle `C:\Program Files\Cppcheck\`'tir).

### 7.1 Cppcheck'i PATH'e Ekleme

Windows kurulum dosyası Cppcheck'i otomatik olarak PATH ortam değişkenine eklemez; bu yüzden `cppcheck` komutu terminalde doğrudan tanınmaz. Aşağıdaki komutu **yönetici olarak açılmış** bir PowerShell'de bir kere çalıştırarak kalıcı olarak PATH'e ekleyin:

```powershell
setx PATH "$($env:PATH);C:\Program Files\Cppcheck" /M
```

> Eğer Cppcheck'i farklı bir dizine kurduysanız `C:\Program Files\Cppcheck` kısmını kendi kurulum yolunuzla değiştirin. .githooks/ klasörü altındaki 'hook_config.py' dosyasındaki cppcheck pathini de güncelleyin.

Komuttan sonra **açık olan tüm terminal pencerelerini kapatıp yeni bir terminal açın** (PATH değişikliği yeni açılan terminallerde geçerli olur). Doğrulamak için:

```powershell
cppcheck --version
```

Bir sürüm numarası dönüyorsa kurulum tamamdır.

---

## 8. Uçtan Uca Doğrulama

Tüm adımları tamamladıktan sonra kurulumun doğru çalıştığını görmek için:

1. `docker ps` ile n8n container'ının `Up` durumda olduğunu kontrol edin.
2. `http://localhost:5678` adresinden n8n arayüzüne girip workflow'ların (main pipeline, agent'lar, bypass report pipeline) yüklü olduğunu görün.
3. Hook'ların kurulu olduğu repo'da, içinde geçerli bir Jira issue key'i olan bir commit mesajıyla küçük bir test değişikliği (bir c kodunda değişiklik) commit edin (örn. `git commit -m "TEST-1: hook testi"`), ve `commit-msg` hook'unun devreye girip build/statik analiz/AI review adımlarını çalıştırdığını gözlemleyin.
4. `cppcheck --version` komutunun terminalde çalıştığını doğrulayın.

---

## 9. Karşılaşabilecek Sorunlar

| Sorun | Çözüm |
|---|---|
| Container ayağa kalkıyor ama intranet servislerine (Jira, dahili LLM) bağlanamıyor / sertifika hatası veriyor | `docker run` komutunda `-v ...aselsan-ca.crt:/certs/aselsan-ca.crt` ve `-e NODE_EXTRA_CA_CERTS="/certs/aselsan-ca.crt"` satırlarının **ikisinin birden** eklendiğinden emin olun. Bu iki satır olmadan Windows'ta sertifika otomatik tanınmıyor. Eğer sertifika değiştiyse `https://portal.aiplatform.aselsan.com.tr/api-platform` adresinden `Sertifikayı İndir` butonuna basarak güncel sertifikayı indirebilirsiniz. |
| `cppcheck` komutu "tanınmıyor" hatası veriyor | PATH'e ekleme komutunu (Bölüm 7.1) çalıştırdıktan sonra terminali kapatıp yeniden açtığınızdan emin olun. Hâlâ çalışmıyorsa `C:\Program Files\Cppcheck\cppcheck.exe` dosyasının gerçekten var olduğunu kontrol edin. |
| Docker Desktop kurulmuyor / açılmıyor / WSL hatası veriyor | Docker Desktop'ın 4.48.0 veya öncesi bir sürüm olduğundan (Windows sürümünüzle uyumlu olduğundan) ve WSL 2'nin etkin olduğundan emin olun (`wsl --status`). |
| MISRA addon çalışmıyor / "Python addons" hatası | Cppcheck'i kaldırıp kurulumu tekrar başlatın ve sihirbazda "Python addons" seçeneğini işaretlediğinizden emin olun. |
| MISRA sonuçları içinde `Required` veya `Advisory` bilgisi yerine `Undefined` yazıyor | `misra_c_2023__headlines_for_cppcheck.txt` dosyasının `.githooks/` klasörü altında bulunduğundan emin olun. `.githooks/hook_config.py` içindeki "rule text" path'inin doğru olduğundan emin olun. |
