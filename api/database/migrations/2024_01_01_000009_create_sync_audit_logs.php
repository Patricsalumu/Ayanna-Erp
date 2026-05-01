<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('sync_audit_logs', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('table_name');
            $table->string('record_id');
            $table->string('operation'); // INSERT | UPDATE | DELETE
            $table->json('client_data')->nullable();
            $table->json('server_data_before')->nullable();
            $table->boolean('conflict_resolved')->default(false);
            $table->timestamp('client_updated_at')->nullable();
            $table->uuid('synced_by')->nullable()->index();
            $table->timestamps();
            $table->softDeletes();

            $table->index(['table_name', 'record_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('sync_audit_logs');
    }
};
