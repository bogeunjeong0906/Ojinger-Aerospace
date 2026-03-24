# 로켓 모델링 입력 파라미터 정리

본 문서는 현재 `export.ks`가 실제로 내보내는 값과, 그 값을 바탕으로 Python 측에서 계산해야 하는 값을 구분한다. 핵심 원칙은 다음과 같다.

- base kOS API로 안전하게 직접 얻을 수 있는 값만 export한다.
- 직접 보장하기 어려운 고수준 값은 Python 모델이 exported seed parameters로 계산한다.
- 문서상 필수 모델링 값과 실제 export 필드는 동일한 개념이 아니다.

---

## 1. 직접 export되는 로켓 레벨 seed
- `rocket`
- `rocketInfo.name`
- `rocketInfo.vesselType`
- `rocketInfo.wetMass`
- `rocketInfo.dryMass`
- `rocketInfo.stageNum`
- `rocketInfo.partCount`
- `rocketInfo.engineCount`

이 값들은 전체 로켓 식별과 질량 초기조건의 seed로 사용한다.

## 2. 직접 export되는 천체 및 발사 환경 seed
- `body.name`
- `body.mass`
- `body.radius`
- `body.mu`
- `body.hasOcean`
- `body.hasSolidSurface`
- `body.rotationPeriod`
- `body.soiRadius`
- `body.atmosphereExists`
- `body.launchLatitude`
- `body.launchLongitude`
- `body.launchAltitude`
- `body.launchTerrainHeight`
- `body.localGravity`
- `body.atmHeight`
- `body.atmMolarMass`
- `body.atmAdiabaticIndex`
- `body.atmOxygen`
- `body.atmPressureSeaLevel`
- `body.launchPressure`
- `body.launchTemperature`
- `body.atmProfile[]`

`atmProfile`은 고도별 압력/온도 lookup table이므로 Python 측 대기 모델 보간 입력으로 사용한다.

## 3. 직접 export되는 stage 레벨 seed
각 stage마다 다음 구조가 제공된다.

- `stage`
- `parts[]`
- `partDetails[]`
- `engines[]`
- `tanks[]`
- `sim`

그 중 모델링에 직접 쓰이는 핵심 seed는 `sim`과 `engines`, `tanks`다.

### 3.1 sim 필드
- `currentMass`
- `dryMass`
- `wetMass`
- `engineCount`
- `maxThrust`
- `maxMassFlow`
- `maxFuelFlow`
- `vacuumIsp`
- `seaLevelIsp`
- `fuelMass`
- `oxidizerMass`
- `localGravity`
- `twrSurfaceWet`
- `twrSurfaceCurrent`
- `resourceAmounts`
- `resourceCapacities`
- `resourceMasses`
- `resourceCapacityMasses`

### 3.2 engine seed
각 엔진은 다음 값을 가진다.

- `name`
- `title`
- `uid`
- `stage`
- `currentMass`
- `dryMass`
- `wetMass`
- `maxThrust`
- `vacuumIsp`
- `seaLevelIsp`
- `maxMassFlow`
- `maxFuelFlow`
- `propellantMix[]`

### 3.3 tank and resource seed
각 tank는 part 질량과 resource breakdown을 함께 제공한다.

- `partName`
- `partTitle`
- `partUid`
- `stage`
- `partMassCurrent`
- `partMassDry`
- `partMassWet`
- `resources[]`

각 resource는 다음 값을 가진다.

- `name`
- `amount`
- `capacity`
- `density`
- `mass`
- `capacityMass`

## 4. 직접 export되지 않는 값
아래 값들은 현재 구현에서 직접 export되지 않으며, 문서상 직접 획득 가능하다고 간주하면 안 된다.

- exact `length`
- exact `diameter`
- `reference_area`
- `drag_coefficient`
- `payload_mass`
- high-confidence `deltaV`
- high-confidence `burn_time`

이 값들은 base kOS API 기준으로 unsafe 하거나, 정의 자체가 추정에 의존하거나, 현재 스크립트가 일부 propellant만 반영하는 식의 불완전 계산을 하지 않도록 제외된 항목이다.

## 5. Python 측 계산 대상으로 보는 값
다음 값들은 export.ks가 직접 결과를 주지 않고, Python 모델이 seed로부터 계산해야 한다.

- stage별 상세 deltaV
- burn time 근사 또는 mission-specific burn profile
- 공력 단면적 및 drag 관련 파라미터
- payload 분리 규칙이 필요한 질량 분해값
- 로켓 전체 형상 기반 length, diameter

즉, 현재 export 계약은 "완성된 로켓 해석 결과"가 아니라 "안전하게 검증 가능한 입력 seed 세트"다.

---

> 모델링 코드에서는 직접 export된 값과 Python 후처리 계산값을 명확히 분리해야 한다. export.ks에 없는 값을 문서상 이미 보장된 값처럼 취급하면 구현과 문서가 다시 불일치하게 된다.
