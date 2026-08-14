<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('core_enterprises', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('name', 255);
            $table->text('address')->nullable();
            $table->string('phone', 50)->nullable();
            $table->string('email', 100)->nullable();
            $table->string('rccm', 100)->nullable();
            $table->string('id_nat', 100)->nullable();
            $table->longText('logo')->nullable();
            $table->text('slogan')->nullable();
            $table->string('currency', 10)->default('USD');
            $table->decimal('taux_de_change', 12, 4)->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('modules', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('name', 100)->unique();
            $table->text('description')->nullable();
            $table->timestamps();
            $table->softDeletes();
        });

        Schema::create('core_users', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('enterprise_id')->constrained('core_enterprises')->cascadeOnDelete();
            $table->string('name', 255);
            $table->string('email', 100)->unique();
            $table->string('password', 255);
            $table->string('role', 50)->default('admin');
            $table->json('modules')->nullable();
            $table->timestamps();
            $table->softDeletes();
            $table->index('enterprise_id');
        });

        Schema::create('core_pos_points', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('enterprise_id')->constrained('core_enterprises')->cascadeOnDelete();
            $table->foreignUuid('module_id')->constrained('modules');
            $table->string('name', 255);
            $table->timestamps();
            $table->softDeletes();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('core_pos_points');
        Schema::dropIfExists('core_users');
        Schema::dropIfExists('modules');
        Schema::dropIfExists('core_enterprises');
    }
};
