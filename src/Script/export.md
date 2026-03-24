export.ks 기술정의서

구현시 주의사항
- kOS는 Python과 문법이 다르므로 KOS_DOC 기준으로 command와 suffix를 사용해야 한다.
- 이 문서는 현재 구현된 export.ks의 실제 JSON 출력 구조만 설명한다.
- 문서에 없는 고수준 값은 export.ks가 직접 보장하지 않으며, 필요 시 Python 쪽에서 후처리해야 한다.

이 파일은 부트파일이다. 로켓이 발사대에서 조립된 직후 실행되어 현재 선체와 발사 환경 정보를 JSON으로 내보낸다.

## 1. 출력 파일
- 파일명은 항상 로켓 이름 기반이며 `<rocket_name>.json` 형식이다.
- 현재 구현은 같은 JSON을 다음 두 위치에 모두 저장한다.
- `0:/<rocket_name>.json`
- `1:/<rocket_name>.json`

## 2. 최상위 JSON 구조

```json
{
	"rocket": "<rocket_name>",
	"rocketInfo": { ... },
	"body": { ... },
	"stages": [ ... ]
}
```

### 2.1 rocket
- 문자열 한 개이며, 현재 선체 이름을 그대로 기록한다.

### 2.2 rocketInfo
- `name`
- `vesselType`
- `wetMass`
- `dryMass`
- `stageNum`
- `partCount`
- `engineCount`

### 2.3 body
- 기본 천체 값
- `name`
- `mass`
- `radius`
- `mu`
- `hasOcean`
- `hasSolidSurface`
- `rotationPeriod`
- `soiRadius`

- 발사 시점 위치 및 중력 seed
- `atmosphereExists`
- `launchLatitude`
- `launchLongitude`
- `launchAltitude`
- `launchTerrainHeight`
- `localGravity`

- 대기 관련 값
- `atmHeight`
- `atmMolarMass`
- `atmAdiabaticIndex`
- `atmOxygen`
- `atmPressureSeaLevel`
- `launchPressure`
- `launchTemperature`
- `atmProfile`

`atmProfile`은 고도 1000m 간격의 리스트이며 각 원소는 아래 구조를 가진다.

```json
{
	"alt": 0,
	"pressure": 0,
	"temperature": 0
}
```

대기가 없는 천체에서는 관련 필드가 0 또는 `false`로 기록되고, `atmProfile`은 빈 리스트가 된다.

### 2.4 stages
각 원소는 하나의 stage를 나타내며 아래 구조를 가진다.

```json
{
	"stage": 0,
	"parts": ["..."],
	"partDetails": [ ... ],
	"engines": [ ... ],
	"tanks": [ ... ],
	"sim": { ... }
}
```

#### parts
- 해당 stage에 속한 part name 문자열 리스트다.

#### partDetails
각 part에 대해 다음 필드를 기록한다.
- `name`
- `title`
- `uid`
- `tag`
- `stage`
- `currentMass`
- `dryMass`
- `wetMass`
- `modules`

#### engines
엔진은 `SHIP:ENGINES` 기준으로 수집하며, 각 원소는 다음 필드를 가진다.
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
- `propellantMix`

`propellantMix`의 각 원소는 다음 구조다.

```json
{
	"name": "LiquidFuel",
	"ratio": 0,
	"density": 0
}
```

#### tanks
리소스를 하나 이상 가진 part만 tank 항목으로 내보낸다. 각 tank는 다음 필드를 가진다.
- `partName`
- `partTitle`
- `partUid`
- `stage`
- `partMassCurrent`
- `partMassDry`
- `partMassWet`
- `resources`

`resources`의 각 원소는 다음 구조다.

```json
{
	"name": "LiquidFuel",
	"amount": 0,
	"capacity": 0,
	"density": 0,
	"mass": 0,
	"capacityMass": 0
}
```

#### sim
`sim`은 Python 쪽 모델링 계산을 위한 stage seed 파라미터다.
- `stage`
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

## 3. 현재 구현이 의도적으로 직접 내보내지 않는 값
- exact `length`
- exact `diameter`
- `reference_area`
- `drag_coefficient`
- `payload_mass`
- high-confidence `deltaV`

위 값들은 현재 export.ks가 사용하는 base kOS API만으로 안전하게 직접 보장할 수 없으므로, 문서상 직접 export된다고 주장하지 않는다.

## 4. Python 측 계산 원칙
- 직접 얻기 어려운 고수준 modeling 값은 export.ks가 seed 파라미터만 제공한다.
- Python 측에서 `rocketInfo`, `body`, 각 stage의 `engines`, `tanks`, `sim`을 사용해 필요한 파생치를 계산한다.
- 따라서 이 문서는 "모든 시뮬레이션 결과를 export한다"가 아니라 "안전한 원시값과 파생 seed를 export한다"는 계약으로 해석해야 한다.


    