
Select *
From portfolioproject..CovidDeaths
WHERE continent is not null
Order by 3,4

Select *
From portfolioproject..CovidVaccinations
order by 3,4


-- Select data that we are going to be using
Select Location, date, total_cases, new_cases, total_deaths, population 
From portfolioproject..CovidDeaths
order by 1,2;


-- Looking at total cases vs total deaths
Select Location, date, total_cases, new_cases, total_deaths, (total_deaths/total_cases)*100 as DeathPercentage 
From portfolioproject..CovidDeaths
Where location like 'India'
order by 1,2;

-- Looking at total cases vs population
-- Shows what percentage of population got covid
Select Location, date, total_cases, population, total_cases, (total_deaths/total_cases)*100 as DeathPercentage 
From portfolioproject..CovidDeaths
Where location like 'India'
order by 1,2;

-- Looking at countries with highest infection rate compared to population

Select Location, population, MAX(total_cases) as HighestInfectionCount, Max((total_cases/population))*100 as PercentagePopulationInfected 
From portfolioproject..CovidDeaths
-- Where location like 'India'
group by Location, population
order by PercentagePopulationInfected desc;

-- Showing Countries with highest death count per population

Select Location, MAX(cast(total_deaths as int)) as TotalDeathCount
From portfolioproject..CovidDeaths
-- Where location like 'India'
where continent is not null
group by Location
order by TotalDeathCount desc;

-- Sorting according to continents
-- Showing continents with highesst death count per population

Select continent, MAX(cast(total_deaths as int)) as TotalDeathCount
From portfolioproject..CovidDeaths
-- Where location like 'India'
where continent is null
group by continent
order by TotalDeathCount desc;

-- Global Numbers
Select SUM(new_cases) as total_cases, SUM(cast(new_deaths as int)) as total_deaths, SUM(cast(new_deaths as int))/SUM(New_Cases)*100 as DeathPercentage 
From portfolioproject..CovidDeaths
where continent is not null 
order by 1,2;

-- Using CTE
-- Total Population vs Vaccinations

With PopvsVac (Continent, Location, Date, Population, new_vaccinations, RollingPeopleVaccinated)
as
(
Select dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations,
 SUM(CONVERT(bigint,vac.new_vaccinations)) OVER(Partition by dea.Location Order by dea.location,
 dea.Date) as RollingPeopleVaccinated
 From portfolioproject..CovidDeaths dea
 Join portfolioproject..CovidVaccinations vac
	On dea.location = vac.location
	and dea.date = vac.date
where dea.continent is not null 
)
Select *, RollingPeopleVaccinated/Population
From PopvsVac

-- TEMP Tables

DROP Table if exists #PercentPopulationVaccinated
Create Table #PercentPopulationVaccinated
(
Continent nvarchar(255),
Location nvarchar(255),
Date datetime,
Population numeric,
new_vaccinations numeric,
RollingPeopleVaccinated numeric
)

Insert into #PercentPopulationVaccinated
Select dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations,
 SUM(CONVERT(bigint,vac.new_vaccinations)) OVER(Partition by dea.Location Order by dea.location,
 dea.Date) as RollingPeopleVaccinated
 From portfolioproject..CovidDeaths dea
 Join portfolioproject..CovidVaccinations vac
	On dea.location = vac.location
	and dea.date = vac.date
-- where dea.continent is not null 

Select *, (RollingPeopleVaccinated/Population) *100
From #PercentPopulationVaccinated


-- Creating View to store data for later visualizations
DROP View if exists PercentPopulationVaccinated

Create View PercentPopulationVaccinated1 as 
Select dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations,
 SUM(CONVERT(bigint,vac.new_vaccinations)) OVER(Partition by dea.Location Order by dea.location,
 dea.Date) as RollingPeopleVaccinated
 From portfolioproject..CovidDeaths dea
 Join portfolioproject..CovidVaccinations vac
	On dea.location = vac.location
	and dea.date = vac.date
where dea.continent is not null
-- order by 2,3


Select *
From PercentPopulationVaccinated1