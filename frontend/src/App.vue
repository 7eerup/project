<template>
  <div class="container">
    <div v-if="step < steps.length">
      <div class="progress-bar">
        <div class="progress" :style="{ width: ((step + 1) / steps.length) * 100 + '%' }"></div>
      </div>
      <div class="question-card">
        <h2 class="question-title">{{ steps[step].title }}</h2>
        <p v-if="steps[step].subtitle" class="question-subtitle">{{ steps[step].subtitle }}</p>
        
        <div class="options">
          <template v-for="(option, idx) in steps[step].options" :key="idx">
            <label class="option-label" :class="{ selected: surveyData[steps[step].key] === getOptionValue(option) }">
              <input
                v-if="steps[step].inputType === 'select'"
                type="radio"
                :name="steps[step].key"
                :value="getOptionValue(option)"
                v-model="surveyData[steps[step].key]"
              />
              <div class="label-text">
                <template v-if="option.label">{{ option.label }}</template>
                <template v-else-if="typeof option === 'string'">{{ option }}</template>
              </div>
            </label>
          </template>
        </div>

        <div v-if="steps[step].inputType === 'text'" class="open-input">
          <input type="text" v-model="surveyData[steps[step].key]" :placeholder="steps[step].placeholder" class="text-input" />
        </div>

        <div class="btn-group">
          <button v-if="step > 0" class="prev-btn" @click="goPrev">이전</button>
          <button class="next-btn" :disabled="!canProceedStep" @click="goNext">
            {{ step === steps.length - 1 ? '결과 보기' : '다음' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="showLoading" class="loading-card">
      <div class="loader"></div>
      <p>견적 분석 중...</p>
    </div>

    <div v-else class="result-card">
      <div class="tabs">
        <button :class="{active: selectedTab === 'resale'}" @click="selectedTab = 'resale'">💰 중고가 방어</button>
        <button :class="{active: selectedTab === 'upgrade'}" @click="selectedTab = 'upgrade'">🛠️ 업그레이드</button>
        <button :class="{active: selectedTab === 'performance'}" @click="selectedTab = 'performance'">🚀 가성비/특가</button>
      </div>

      <div class="estimate-wrapper" v-if="currentEstimate">
        <div class="estimate-card">
          <h2 class="estimate-title">{{ currentEstimate.option }}</h2>
          <div class="recommend">
            {{ getRecommendText(selectedTab) }}
          </div>
          <table class="parts-table">
            <tr v-for="(part, i) in currentEstimate.parts" :key="i">
              <td class="cat">{{ part.category }}</td>
              <td>{{ part.name }}</td>
            </tr>
          </table>
          <div class="price">{{ currentEstimate.price }}</div>
        </div>
      </div>
      <div v-else class="error-msg">
        데이터를 불러오지 못했습니다.
      </div>

      <div class="summary">
        <h3>📋 입력 정보 요약</h3>
        <ul>
          <li v-for="info in userSummary" :key="info.q">
            <strong>{{ info.q }}:</strong> {{ info.a }}
          </li>
        </ul>
      </div>
      <button class="restart-btn" @click="restartSurvey">처음부터 다시하기</button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue';
import axios from 'axios'; 

const steps = [
  {
    title: 'Q1. 생각하고 계신 컴퓨터 구매 최대 예산은 얼마인가요?',
    subtitle: '(본체 가격 기준입니다)',
    key: 'budget',
    inputType: 'select',
    options: [
      { label: '80만원 이하 (가정/사무용, 가성비)', value: '80만원 이하' },
      { label: '80만원 ~ 120만원 (FHD 게이밍 입문)', value: '80~120만원' },
      { label: '120만원 ~ 180만원 (고화질 게이밍, 영상편집)', value: '120~180만원' },
      { label: '180만원 ~ 250만원 (전문가급 성능)', value: '180~250만원' },
      { label: '250만원 이상 (최상급 하이엔드)', value: '250만원 이상' }
    ]
  },
  {
    title: 'Q2. 컴퓨터를 사용하는 가장 주된 목적은 무엇인가요?',
    key: 'mainUse',
    inputType: 'select',
    options: [
      { label: '사무/웹서핑: 엑셀, 유튜브, 인강', value: '사무/웹서핑' },
      { label: '캐주얼 게임: 롤, 피파, 발로란트', value: '캐주얼 게임' },
      { label: '고사양 게임: 배그, 스팀게임(엘든링)', value: '고사양 게임' },
      { label: '크리에이터: 영상 편집, 디자인', value: '크리에이터' },
      { label: '전문 작업: 3D, 개발, AI, 방송', value: '전문 작업' },
    ]
  },
  {
    title: 'Q3. (선택) 주로 사용하는 특정 프로그램이나 게임 이름을 적어주세요.',
    key: 'favProgramOrGame',
    inputType: 'text',
    placeholder: '예: 로스트아크, 프리미어 프로...'
  },
  {
    title: 'Q4. 원하시는 본체 디자인(감성)이 있나요?',
    key: 'design',
    inputType: 'select',
    options: [
      { label: '상관없음: 성능과 가성비 최우선', value: '상관없음' },
      { label: '블랙 & 심플: 불빛 없이 깔끔', value: '블랙 & 심플' },
      { label: '게이밍 RGB: 화려한 LED', value: '게이밍 RGB' },
      { label: '올 화이트: 케이스/부품 화이트(비용 ↑)', value: '올 화이트' }
    ]
  },
  {
    title: 'Q5. 저장할 파일(사진, 영상, 게임)은 얼마나 되나요?',
    key: 'storage',
    inputType: 'select',
    options: [
      { label: '기본: 게임 1~2개 (500GB)', value: '500GB' },
      { label: '보통: 게임 3~5개 (1TB 추천)', value: '1TB' },
      { label: '많음: 고사양 게임 다수 (2TB+)', value: '2TB 이상' }
    ]
  },
  {
    title: 'Q6. 윈도우(운영체제) 포함 여부를 선택해주세요.',
    subtitle: '(정품 포함 시 약 15~20만원 추가)',
    key: 'windows',
    inputType: 'select',
    options: [
      { label: '포함: 설치 후 배송 (바로 사용)', value: '포함' },
      { label: '미포함: 직접 설치 가능', value: '미포함' }
    ]
  },
  {
    title: 'Q7. 사용하실 모니터의 해상도는 무엇인가요?',
    subtitle: '(모니터 사양에 따라 부품이 달라져요!)',
    key: 'monitor',
    inputType: 'select',
    options: [
      { label: 'FHD (1920x1080): 일반 모니터', value: 'FHD' },
      { label: 'QHD (2560x1440): 고화질 게이밍', value: 'QHD' },
      { label: '4K (3840x2160): 전문가/TV', value: '4K' },
      { label: '모니터도 포함 견적 요청', value: '포함' }
    ]
  },
];

function getOptionValue(option) {
  if (typeof option === 'object' && option.value !== undefined) return option.value;
  return option;
}

const surveyData = reactive({
  budget: '', mainUse: '', favProgramOrGame: '', design: '',
  storage: '', windows: '', monitor: ''
});

const step = ref(0);

const canProceedStep = computed(() => {
  const curr = steps[step.value];
  if (!curr) return false;
  if (curr.inputType === 'text') return true; 
  return !!surveyData[curr.key];
});

function goNext() {
  if (step.value < steps.length - 1) step.value++;
  else startLoading();
}
function goPrev() {
  if (step.value > 0) step.value--;
}

const showLoading = ref(false);

async function startLoading() {
  step.value++; 
  showLoading.value = true; 

  try {
    // [진짜 모드 ON] 주석 해제!
    const response = await axios.post('http://10.19.215.161:5000/build-quote', surveyData);
    answers.value = response.data; // 서버 데이터로 덮어쓰기
    
    // [가짜 모드 OFF] 이 줄은 지우거나 주석 처리하세요
    // await new Promise(resolve => setTimeout(resolve, 3000)); 

  } catch (error) {
    console.error("서버 연결 실패:", error);
    alert("서버 연결 실패! 백엔드가 켜져 있나요?");
  } finally {
    showLoading.value = false;
  }
}

function restartSurvey() {
  Object.keys(surveyData).forEach(k => surveyData[k] = '');
  step.value = 0;
  selectedTab.value = 'resale';
  showLoading.value = false;
}

const selectedTab = ref('resale');

// Mock Data (ref로 감싸져 있는지 확인)
const answers = ref({"resale_set": {"option": "중고가 방어형", "price": "약 140만원", "parts": [{"category": "CPU", "name": "인텔 i7-12700F (중고)"}, {"category": "메인보드", "name": "ASUS TUF GAMING B660M-PLUS WIFI D4"}, {"category": "RAM", "name": "삼성 DDR4 16GB (2x8GB) 3200MHz"}, {"category": "그래픽카드", "name": "이엠텍 RTX 3060 Ti (중고)"}, {"category": "SSD", "name": "마이크론 P3 2TB NVMe"}, {"category": "파워", "name": "시소닉 S12III 650W 80PLUS Bronze"}, {"category": "케이스", "name": "갤럭시 GALAX EX Black RGB"}]}, "upgrade_set": {"option": "업그레이드형", "price": "약 175만원", "parts": [{"category": "CPU", "name": "AMD 라이젠 7 7700X"}, {"category": "메인보드", "name": "MSI MPG B650 TOMAHAWK WIFI"}, {"category": "RAM", "name": "삼성 DDR5 32GB (2x16GB) 5200MHz"}, {"category": "그래픽카드", "name": "MSI RTX 4070 VENTUS 2X"}, {"category": "SSD", "name": "삼성 980 PRO 2TB NVMe"}, {"category": "파워", "name": "시소닉 FOCUS GX-750 80PLUS Gold"}, {"category": "케이스", "name": "Lian Li PC-O11 Dynamic EVO RGB"}]}, "performance_set": {"option": "가성비/특가형", "price": "약 125만원", "parts": [{"category": "CPU", "name": "AMD 라이젠 5 7600"}, {"category": "메인보드", "name": "ASRock B650M PG Riptide"}, {"category": "RAM", "name": "마이크론 DDR5 16GB (2x8GB) 4800MHz"}, {"category": "그래픽카드", "name": "COLORFUL RTX 4060 NB 8GB"}, {"category": "SSD", "name": "SK하이닉스 Platinum P41 2TB NVMe"}, {"category": "파워", "name": "마이크로닉스 Classic II 700W 80PLUS Bronze"}, {"category": "케이스", "name": "앱코 SUITMASTER P150 RGB 강화유리"}]}}
);

const currentEstimate = computed(() => {
  return answers.value[selectedTab.value + '_set'];
});

function getRecommendText(tab) {
  if(tab === 'resale') return "PC 시장에서 가장 인기 있는 부품들입니다. 나중에 중고로 팔 때 가격 방어가 잘 됩니다!";
  if(tab === 'upgrade') return "파워와 메인보드를 빵빵하게 넣었습니다. 3년 뒤에 그래픽카드만 바꿔도 현역입니다.";
  if(tab === 'performance') return "브랜드 거품을 빼고 성능에 몰빵했습니다. 같은 돈으로 게임 프레임이 제일 잘 나옵니다.";
  return "";
}

const userSummary = computed(() => [
  { q: "예산", a: surveyData.budget },
  { q: "주 용도", a: surveyData.mainUse },
  { q: "디자인", a: surveyData.design },
  { q: "모니터", a: surveyData.monitor }
]);
</script>

<style>
body { background: #f9fafb; color: #333; -webkit-font-smoothing: antialiased; }
.container { min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #f9fafb; padding: 24px; }
.progress-bar { width: 100%; max-width: 360px; height: 6px; background: #e9ecef; border-radius: 3px; margin: 0 auto 16px; overflow: hidden; }
.progress { background: #4872f2; height: 100%; transition: width 0.4s; }
.question-card, .loading-card, .result-card { background: #fff; border-radius: 16px; padding: 32px 28px 24px 28px; width: 100%; max-width: 420px; box-shadow: 0 6px 20px 0 #a1afc933; margin: 20px 0; text-align: center; }
.question-title { font-size: 1.3rem; font-weight: 700; margin-bottom: 8px; color: #111; }
.question-subtitle { color: #666; font-size: 0.95rem; margin-bottom: 20px; font-weight: 500; }
.options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; }
.option-label { display: flex; align-items: center; justify-content: center; background: #f1f3f7; border-radius: 10px; padding: 14px; cursor: pointer; border: 2px solid transparent; transition: all 0.2s; color: #333; font-weight: 600; font-size: 1rem; }
.option-label:hover { background: #e8ebf2; }
.option-label.selected { background: #e6ebfc; border-color: #4872f2; color: #243070; font-weight: 700; }
.option-label input { display: none; }
.label-text { display: block; width: 100%; text-align: center; }
.open-input { margin-bottom: 20px; }
.text-input { width: 90%; padding: 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 1rem; outline: none; }
.btn-group { display: flex; gap: 10px; justify-content: center; }
.next-btn, .prev-btn { flex: 1; border: none; border-radius: 8px; padding: 12px 0; font-size: 1rem; font-weight: 600; cursor: pointer; transition: 0.2s; }
.next-btn { background: #4872f2; color: #fff; box-shadow: 0 2px 8px #4872f244; }
.next-btn:disabled { background: #c6ccdd; cursor: not-allowed; box-shadow: none; }
.prev-btn { background: #eef1fa; color: #5a6b8c; }
.loading-card .loader { border: 6px solid #f3f3f3; border-top: 6px solid #4872f2; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 16px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.tabs { display: flex; gap: 5px; margin-bottom: 20px; flex-wrap: wrap; justify-content: center;}
.tabs button { flex: 1; background: #f1f3f7; border: none; border-radius: 8px; padding: 10px; font-size: 0.95rem; color: #555; cursor: pointer; white-space: nowrap; font-weight: 600; }
.tabs button.active { background: #4872f2; color: #fff; font-weight: 700; }
.estimate-card { background: #f9fbff; border: 1px solid #dce4f2; border-radius: 12px; padding: 20px; text-align: left; margin-bottom: 20px; }
.estimate-title { font-size: 1.2rem; font-weight: 800; margin-bottom: 10px; color: #1a202c; }
.recommend { background: #eef4fc; padding: 12px; border-radius: 8px; font-size: 0.95rem; color: #2a4365; margin-bottom: 16px; line-height: 1.5; font-weight: 600; border: 1px solid #d1deed; }
.parts-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
.parts-table td { padding: 8px 0; border-bottom: 1px solid #e2e8f0; color: #2d3748; }
.parts-table td.cat { font-weight: 700; color: #4872f2; width: 90px; vertical-align: top; }
.price { text-align: right; font-weight: 800; font-size: 1.3rem; color: #2b6cb0; margin-top: 16px; }
.summary { background: #f7fafc; border: 1px solid #edf2f7; border-radius: 8px; padding: 16px; margin-top: 24px; text-align: left; font-size: 0.95rem; color: #2d3748; }
.summary h3 { margin-bottom: 10px; color: #1a202c; }
.summary li { margin-bottom: 4px; line-height: 1.4; }
.restart-btn { margin-top: 24px; background: #fff; border: 1px solid #cbd5e0; padding: 10px 20px; border-radius: 6px; cursor: pointer; color: #4a5568; font-weight: 600; }
.restart-btn:hover { background: #f7fafc; }
</style>