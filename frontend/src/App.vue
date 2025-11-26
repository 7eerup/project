<template>
  <div class="container">
    <img :src="loadingLogo" class="top-logo" alt="서비스 로고" />

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

        <div v-if="step === 0" class="warning-banner">
          ⚠️ 선택하신 예산 내에서 최적의 성능을 구성하기 위해,<br>
          일부 부품 등급이 조정될 수 있습니다.<br>
          <span class="sub-text">(예: 80만원 예산으로 4K 게이밍 구성 시)</span>
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
      <div class="loading-wrapper">
        <div class="spinner-ring"></div>
        <img :src="loadingLogo" class="center-logo" alt="Logo" />
      </div>
      <p>견적 분석 중...</p>
      <p class="loading-sub">부품 간 호환성을 정밀하게 체크하고 있습니다...</p>
    </div>

    <div v-else class="result-card">
      <div class="tabs">
        <button :class="{active: selectedTab === 'resale'}" @click="selectedTab = 'resale'">💰 중고가 방어</button>
        <button :class="{active: selectedTab === 'upgrade'}" @click="selectedTab = 'upgrade'">🛠️ 업그레이드</button>
        <button :class="{active: selectedTab === 'performance'}" @click="selectedTab = 'performance'">🚀 퍼포먼스</button>
      </div>

      <div class="estimate-wrapper" v-if="currentEstimate">
        <div class="estimate-card">
          <h2 class="estimate-title">{{ currentEstimate.option }}</h2>
          <div class="recommend">
            {{ getRecommendText(selectedTab) }}
          </div>
          <table class="parts-table">
            <tr v-for="(part, i) in currentEstimate.parts" :key="i">
              <td class="cat">
                {{ part.category }}
                <span class="tooltip-icon" v-if="getTooltipText(part.category)">
                  ?
                  <span class="tooltip-text">{{ getTooltipText(part.category) }}</span>
                </span>
              </td>
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
import loadingLogo from '@/assets/logo.png'; 

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
    title: 'Q6. 사용하실 모니터의 해상도는 무엇인가요?',
    subtitle: '(주 사용프로그램에서 최대로 사용할 해상도를 알려주세요)',
    key: 'monitor',
    inputType: 'select',
    options: [
      { label: 'FHD (1920x1080): 일반 모니터', value: 'FHD' },
      { label: 'QHD (2560x1440): 고화질 게이밍', value: 'QHD' },
      { label: '4K (3840x2160): 전문가/TV', value: '4K' },
    ]
  },
];

function getOptionValue(option) {
  if (typeof option === 'object' && option.value !== undefined) return option.value;
  return option;
}

const surveyData = reactive({
  budget: '', mainUse: '', favProgramOrGame: '', design: '',
  storage: '', monitor: ''
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
    const API = import.meta.env.VITE_API_URL;
    const response = await axios.post(`${API}/build-quote`, surveyData);
    answers.value = response.data; // 서버 데이터로 덮어쓰기
    // await new Promise(resolve => setTimeout(resolve, 3000));
  } catch (error) {
    console.error("서버 연결 실패:", error);
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

// Mock Data
const answers = ref({
  resale_set: {
    option: "중고가 방어형",
    parts: [
      { category: "CPU", name: "인텔 i5-13400F" },
      { category: "메인보드", name: "ASUS PRIME B760M-A" },
      { category: "RAM", name: "삼성 DDR4 16GB (8GBx2)" },
      { category: "그래픽카드", name: "이엠텍 지포스 RTX 4060" },
      { category: "SSD", name: "삼성 980 1TB" },
      { category: "파워", name: "마이크로닉스 600W" },
      { category: "케이스", name: "앱코 NCORE 베놈" }
    ],
    price: "약 120만원"
  },
  upgrade_set: {
    option: "업그레이드형",
    parts: [
      { category: "CPU", name: "AMD 라이젠5 7500F" },
      { category: "메인보드", name: "MSI PRO B650M-A" },
      { category: "RAM", name: "삼성 DDR5 32GB" },
      { category: "그래픽카드", name: "MSI RTX 4060 Ti" },
      { category: "SSD", "name": "SK하이닉스 P31 1TB" },
      { category: "파워", name: "시소닉 850W" },
      { category: "케이스", name: "darkFlash DLX21" }
    ],
    price: "약 155만원"
  },
  performance_set: {
    option: "가성비/특가형",
    parts: [
      { category: "CPU", name: "인텔 i5-12400F" },
      { category: "메인보드", name: "ASRock B660M" },
      { category: "RAM", name: "DDR4 16GB" },
      { category: "그래픽카드", name: "COLORFUL RTX 4060" },
      { category: "SSD", name: "마이크론 1TB" },
      { category: "파워", name: "잘만 600W" },
      { category: "케이스", name: "DAVEN D6" }
    ],
    price: "약 108만원"
  }
});

const currentEstimate = computed(() => {
  return answers.value[selectedTab.value + '_set'];
});

function getRecommendText(tab) {
  if(tab === 'resale') return "가장 범용적이고, 호환성이 좋은 부품들로 구성했습니다. 추후 중고 거래 시에도 유리합니다.";
  if(tab === 'upgrade') return "향후 부품 교체를 고려하여, 확장성과 호환성이 뛰어난 부품 위주로 선택했습니다.";
  if(tab === 'performance') return "브랜드 인지도보다는 실제 성능에 집중했습니다. 현 시점에서 가격 대비 성능이 가장 뛰어납니다.";
  return "";
}

function getTooltipText(category) {
  const use = surveyData.mainUse || "";
  const monitor = surveyData.monitor || "";
  
  if (category.includes('CPU')) {
    if (use.includes('크리에이터') || use.includes('전문 작업')) {
      return "영상 편집과 렌더링은 '멀티코어' 성능이 핵심입니다. 코어 수가 넉넉한 고성능 프로세서를 우선했습니다.";
    }
    if (use.includes('고사양 게임') || use.includes('캐주얼 게임')) {
      return "게임 성능은 '단일 코어 클럭'이 결정적인 요소입니다. 그래픽카드 성능을 온전히 끌어낼 수 있는 모델을 선택했습니다.";
    }
    return "사무용 작업에 최적화된, 가성비와 안정성이 검증된 프로세서입니다.";
  }
  if (category.includes('RAM')) {
    if (use.includes('크리에이터') || use.includes('전문 작업')) {
      return "프리미어 프로, 3D 렌더링 시 16GB는 부족할 수 있습니다. 쾌적한 작업을 위해 32GB 이상을 권장합니다.";
    }
    if (use.includes('고사양 게임')) {
      return "대부분의 고사양 게임은 16GB로 충분하지만, 32GB는 더 여유롭습니다. 성능 향상을 위해 '듀얼 채널'로 구성했습니다.";
    }
    return "웹서핑과 사무 작업에는 16GB로도 매우 충분합니다. 쾌적한 멀티태스킹이 가능합니다.";
  }
  if (category.includes('그래픽')) {
    if (monitor === '4K') {
      return "4K 해상도에서는 VRAM(비디오 메모리) 용량이 성능에 가장 큰 영향을 미칩니다. 고사양 모델이 필수적입니다.";
    }
    if (use.includes('전문 작업') || use.includes('크리에이터')) {
      return "작업 효율을 위해 CUDA 가속 기능이 우수한 NVIDIA 계열 그래픽카드를 추천합니다.";
    }
    if (use.includes('사무')) {
      return "사무용으로는 내장 그래픽이나 기본형 카드로 충분합니다. 불필요한 전력 소모를 줄였습니다.";
    }
    return "게임 프레임 유지를 위한 핵심 부품입니다. 예산 내에서 가장 성능이 좋은 칩셋을 선택했습니다.";
  }
  if (category.includes('파워')) {
    if (use.includes('고사양 게임') || use.includes('전문 작업')) {
      return "안정적인 전력 공급을 위해 시스템 총 소모 전력보다 여유 있는 용량으로 구성했습니다.";
    }
    return "시스템 안정성의 핵심입니다. 정격 출력이 보장되지 않는 비정격 제품(일명 뻥파워)은 절대 추천하지 않습니다.";
  }
  if (category.includes('메인보드')) {
    if (selectedTab.value === 'upgrade') {
      return "추후 업그레이드를 고려하여 전원부 구성이 충실하고, 확장성이 뛰어난 모델입니다.";
    }
    return "CPU와의 호환성 및 가성비가 검증된 메인보드 칩셋을 선택했습니다.";
  }
  if (category.includes('케이스')) {
    return "그래픽카드 장착 가능 길이와 메인보드 규격 호환성을 꼼꼼히 체크했습니다. 통기성도 고려되었습니다.";
  }
  return null;
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

.top-logo { width: 80px; height: auto; margin-bottom: 24px; }

/* 배너 스타일 수정: 줄바꿈 후 텍스트 정렬을 위해 line-height 추가 */
.warning-banner { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; margin-top: 16px; font-size: 0.9rem; font-weight: 600; text-align: center; width: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.05); box-sizing: border-box; line-height: 1.6; }
/* 예시 문구(3번째 줄)만 폰트 무게를 살짝 줄여서 가독성 높임 */
.warning-banner .sub-text { font-weight: 400; font-size: 0.85rem; color: #856404; }

.progress-bar { width: 100%; max-width: 360px; height: 6px; background: #e9ecef; border-radius: 3px; margin: 0 auto 16px; overflow: hidden; }
.progress { background: #4872f2; height: 100%; transition: width 0.4s; }
.question-card, .loading-card, .result-card { background: #fff; border-radius: 16px; padding: 32px 28px 24px 28px; width: 100%; max-width: 420px; box-shadow: 0 6px 20px 0 #a1afc933; margin: 20px 0; text-align: center; box-sizing: border-box; }
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

.loading-wrapper { position: relative; width: 90px; height: 90px; margin: 0 auto 20px; }
.spinner-ring { box-sizing: border-box; width: 100%; height: 100%; border-radius: 50%; border: 4px solid #f3f3f3; border-top: 4px solid #4872f2; animation: spin 1.2s linear infinite; position: absolute; top: 0; left: 0; }
.center-logo { width: 50%; height: auto; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.loading-sub { font-size: 0.9rem; color: #888; margin-top: 8px; }
.tabs { display: flex; gap: 5px; margin-bottom: 20px; flex-wrap: wrap; justify-content: center;}
.tabs button { flex: 1; background: #f1f3f7; border: none; border-radius: 8px; padding: 10px; font-size: 0.95rem; color: #555; cursor: pointer; white-space: nowrap; font-weight: 600; }
.tabs button.active { background: #4872f2; color: #fff; font-weight: 700; }
.estimate-card { background: #f9fbff; border: 1px solid #dce4f2; border-radius: 12px; padding: 20px; text-align: left; margin-bottom: 20px; }
.estimate-title { font-size: 1.2rem; font-weight: 800; margin-bottom: 10px; color: #1a202c; }
.recommend { background: #eef4fc; padding: 12px; border-radius: 8px; font-size: 0.95rem; color: #2a4365; margin-bottom: 16px; line-height: 1.5; font-weight: 600; border: 1px solid #d1deed; }
.parts-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
.parts-table td { padding: 8px 0; border-bottom: 1px solid #e2e8f0; color: #2d3748; }
.parts-table td.cat { font-weight: 700; color: #4872f2; width: 110px; vertical-align: top; position: relative; }
.price { text-align: right; font-weight: 800; font-size: 1.3rem; color: #2b6cb0; margin-top: 16px; }
.summary { background: #f7fafc; border: 1px solid #edf2f7; border-radius: 8px; padding: 16px; margin-top: 24px; text-align: left; font-size: 0.95rem; color: #2d3748; }
.summary h3 { margin-bottom: 10px; color: #1a202c; }
.summary li { margin-bottom: 4px; line-height: 1.4; }
.restart-btn { margin-top: 24px; background: #fff; border: 1px solid #cbd5e0; padding: 10px 20px; border-radius: 6px; cursor: pointer; color: #4a5568; font-weight: 600; }
.restart-btn:hover { background: #f7fafc; }
.tooltip-icon { display: inline-block; width: 18px; height: 18px; line-height: 18px; background: #ccc; color: #fff; border-radius: 50%; text-align: center; font-size: 0.8rem; font-weight: bold; margin-left: 4px; cursor: help; position: relative; }
.tooltip-icon:hover { background: #4872f2; }
.tooltip-icon .tooltip-text { visibility: hidden; width: 220px; background-color: #333; color: #fff; text-align: left; border-radius: 6px; padding: 10px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -110px; opacity: 0; transition: opacity 0.3s; font-weight: 400; font-size: 0.85rem; line-height: 1.4; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
.tooltip-icon:hover .tooltip-text { visibility: visible; opacity: 1; }
.tooltip-icon .tooltip-text::after { content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: #333 transparent transparent transparent; }

@media (max-width: 480px) {
  .container { padding: 16px; }
  .question-card, .loading-card, .result-card { padding: 24px 20px; }
  .question-title { font-size: 1.2rem; }
  .option-label { padding: 12px; font-size: 0.95rem; }
  .warning-banner { font-size: 0.85rem; padding: 10px 16px; }
  .parts-table td.cat { width: 90px; font-size: 0.9rem; }
  .tooltip-icon .tooltip-text { width: 180px; margin-left: -90px; }
}
</style>