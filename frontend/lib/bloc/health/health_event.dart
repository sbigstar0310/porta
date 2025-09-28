abstract class HealthEvent {}

class HealthCheckRequested extends HealthEvent {}

class HealthDbCheckRequested extends HealthEvent {}

class HealthReset extends HealthEvent {}
